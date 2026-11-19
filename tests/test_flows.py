"""
End-to-End flow tests verifying all verification scenarios required:
1. Weak vs strong registration
2. Duplicate email registration rejection
3. 5 failed login attempts triggering account lockout
4. Forgot password token flow, single-use enforcement, and expiration rejection
5. Unauthenticated access control check
6. Multi-tenant history isolation
7. Grade-adaptive doubt resolution for lower (1-5), middle (6-10), senior (11-12) & image doubts
"""

import os
import tempfile
import pytest
from PIL import Image
import auth
import db
import llm
import prompts


@pytest.fixture
def flow_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.init_db(path)
    yield path
    try:
        os.remove(path)
    except Exception:
        pass


def test_flow_1_weak_vs_strong_registration(flow_db):
    """Flow 1: Register with a weak password (should fail), then strong (should succeed)."""
    # 1. Weak password (no number/special)
    is_valid, msg = auth.validate_registration_inputs(
        name="Vikram Patel",
        email="vikram@example.com",
        username="vikram123",
        class_level=8,
        board="CBSE",
        password="weakpassword",
        confirm_password="weakpassword",
        terms_agreed=True,
        db_path=flow_db
    )
    assert is_valid is False
    assert "not strong enough" in msg.lower()

    # 2. Strong password
    is_valid_strong, _ = auth.validate_registration_inputs(
        name="Vikram Patel",
        email="vikram@example.com",
        username="vikram123",
        class_level=8,
        board="CBSE",
        password="VikramPass@2026",
        confirm_password="VikramPass@2026",
        terms_agreed=True,
        db_path=flow_db
    )
    assert is_valid_strong is True

    # Save user to DB
    uid = db.create_user(
        name="Vikram Patel",
        email="vikram@example.com",
        username="vikram123",
        password_hash=auth.hash_password("VikramPass@2026"),
        class_level=8,
        board="CBSE",
        db_path=flow_db
    )
    assert uid > 0


def test_flow_2_duplicate_email_registration(flow_db):
    """Flow 2: Register with a duplicate email (should fail)."""
    # Register first user
    db.create_user(
        name="Pooja Sharma",
        email="pooja@example.com",
        username="pooja_s",
        password_hash=auth.hash_password("PoojaPass@123"),
        class_level=9,
        board="ICSE",
        db_path=flow_db
    )

    # Attempt to register second user with same email (different case to verify case-insensitivity)
    is_valid, msg = auth.validate_registration_inputs(
        name="Pooja Duplicate",
        email="POOJA@EXAMPLE.COM",
        username="pooja_dup",
        class_level=9,
        board="ICSE",
        password="PoojaPass@123",
        confirm_password="PoojaPass@123",
        terms_agreed=True,
        db_path=flow_db
    )
    assert is_valid is False
    assert "already exists" in msg.lower()


def test_flow_3_login_lockout_and_recovery(flow_db):
    """Flow 3: 5 failed login attempts trigger 15 min lock; unlock on expiry or reset."""
    pwd_raw = "CorrectPassword@123"
    uid = db.create_user(
        name="Lockout Student",
        email="locked@example.com",
        username="locked_student",
        password_hash=auth.hash_password(pwd_raw),
        class_level=11,
        board="CBSE",
        db_path=flow_db
    )

    # 5 failed attempts
    for attempt in range(1, 6):
        db.record_login_failure(uid, max_attempts=5, lock_minutes=15, db_path=flow_db)

    user = db.get_user_by_id(uid, db_path=flow_db)
    is_locked, remaining = db.check_account_locked(user)
    assert is_locked is True
    assert remaining is not None and remaining >= 1

    # After reset / expiration, user can authenticate successfully
    db.reset_login_failures(uid, db_path=flow_db)
    refreshed = db.get_user_by_id(uid, db_path=flow_db)
    is_locked_now, _ = db.check_account_locked(refreshed)
    assert is_locked_now is False
    assert auth.verify_password(pwd_raw, refreshed["password_hash"]) is True


def test_flow_4_forgot_password_and_token_reuse(flow_db):
    """Flow 4: Forgot password, reset using token; token cannot be reused, expired fails."""
    uid = db.create_user(
        name="Reset Test",
        email="reset@example.com",
        username="reset_user",
        password_hash=auth.hash_password("OldPassword@123"),
        class_level=10,
        board="CBSE",
        db_path=flow_db
    )

    # Generate token
    raw_token, token_hash = auth.generate_secure_token()
    db.create_password_reset_entry(uid, token_hash, valid_minutes=20, db_path=flow_db)

    # 1. Verify token exists & is active
    entry = db.verify_reset_token_hash(token_hash, db_path=flow_db)
    assert entry is not None
    assert entry["user_id"] == uid

    # 2. Reset password to new password
    new_pwd = "NewSecurePassword@456"
    new_hash = auth.hash_password(new_pwd)
    db.update_user_password(uid, new_hash, db_path=flow_db)
    db.mark_reset_token_used(token_hash, db_path=flow_db)

    # Verify new password is set
    updated_user = db.get_user_by_id(uid, db_path=flow_db)
    assert auth.verify_password(new_pwd, updated_user["password_hash"]) is True
    assert auth.verify_password("OldPassword@123", updated_user["password_hash"]) is False

    # 3. Confirm token cannot be reused
    entry_reused = db.verify_reset_token_hash(token_hash, db_path=flow_db)
    assert entry_reused is None

    # 4. Confirm expired token is rejected
    raw_exp, hash_exp = auth.generate_secure_token()
    db.create_password_reset_entry(uid, hash_exp, valid_minutes=-10, db_path=flow_db)
    assert db.verify_reset_token_hash(hash_exp, db_path=flow_db) is None


def test_flow_5_unauthenticated_access_protection():
    """Flow 5: Unauthenticated user state has no logged-in user."""
    # Simulation of get_current_user when None
    import streamlit as st
    st.session_state.user = None
    assert auth.get_current_user() is None


def test_flow_6_user_history_isolation(flow_db):
    """Flow 6: One user cannot see or modify another user's history."""
    u1 = db.create_user("User Alpha", "alpha@example.com", "alpha", "hash", 10, "CBSE", db_path=flow_db)
    u2 = db.create_user("User Beta", "beta@example.com", "beta", "hash", 11, "ICSE", db_path=flow_db)

    # Alpha's private session
    s_alpha = "session_alpha_1"
    db.create_chat_session(s_alpha, u1, "Alpha Private Doubt", 10, "CBSE", "Maths", db_path=flow_db)
    db.add_message(s_alpha, "user", "What is Pythagoras theorem?", db_path=flow_db)

    # Beta's private session
    s_beta = "session_beta_1"
    db.create_chat_session(s_beta, u2, "Beta Private Doubt", 11, "ICSE", "Physics", db_path=flow_db)
    db.add_message(s_beta, "user", "Explain Doppler effect", db_path=flow_db)

    # Verification: Alpha sees only Alpha's sessions
    alpha_history = db.get_user_chat_sessions(u1, db_path=flow_db)
    assert len(alpha_history) == 1
    assert alpha_history[0]["id"] == s_alpha
    assert alpha_history[0]["title"] == "Alpha Private Doubt"

    # Beta cannot query Alpha's session
    assert db.get_chat_session(s_alpha, user_id=u2, db_path=flow_db) is None

    # Beta cannot delete Alpha's session
    assert db.delete_chat_session(s_alpha, user_id=u2, db_path=flow_db) is False


def test_flow_7_grade_adaptive_and_image_doubts():
    """Flow 7: Lower class (1-5), middle class (6-10), senior class (11-12) and image doubt."""
    # Lower class (Class 2 Maths)
    ok_lower, resp_lower = llm.generate_doubt_solution(
        doubt_text="Ravi has 7 red apples. His grandmother gives him 5 green apples. How many apples does Ravi have altogether?",
        class_level=2,
        board="CBSE",
        subject="Maths",
        language="English"
    )
    assert ok_lower is True
    assert "Understanding of the Question" in resp_lower
    assert "Step-by-Step Solution" in resp_lower
    assert "Final Answer" in resp_lower
    assert "Practice Questions" in resp_lower

    # Middle class (Class 8 Science)
    ok_middle, resp_middle = llm.generate_doubt_solution(
        doubt_text="Why is water not used to extinguish fires involving electrical equipment?",
        class_level=8,
        board="CBSE",
        subject="Science",
        language="English"
    )
    assert ok_middle is True
    assert "Step-by-Step Solution" in resp_middle
    assert "Common Mistake to Avoid" in resp_middle

    # Senior class (Class 12 Physics)
    ok_senior, resp_senior = llm.generate_doubt_solution(
        doubt_text="State Faraday laws of electromagnetic induction and calculate induced EMF.",
        class_level=12,
        board="CBSE",
        subject="Physics",
        language="English"
    )
    assert ok_senior is True
    assert "Key Concept / Formula Used" in resp_senior

    # Image-based doubt
    test_img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    ok_img, resp_img = llm.generate_doubt_solution(
        doubt_text="Please solve the highlighted question from this page",
        class_level=10,
        board="CBSE",
        subject="Maths",
        image=test_img
    )
    assert ok_img is True
    assert "Practice Questions" in resp_img
