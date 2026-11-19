"""
Unit tests for database functions and multi-tenant isolation.
Uses an isolated temporary SQLite database for test execution.
"""

import os
import tempfile
import datetime
import pytest
import db
import auth


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.init_db(path)
    yield path
    try:
        os.remove(path)
    except Exception:
        pass


def test_user_creation_and_retrieval(temp_db):
    pwd_hash = auth.hash_password("Student@123")
    user_id = db.create_user(
        name="Rohan Gupta",
        email="rohan@example.com",
        username="rohan10",
        password_hash=pwd_hash,
        class_level=10,
        board="CBSE",
        db_path=temp_db
    )
    assert user_id > 0

    user = db.get_user_by_id(user_id, db_path=temp_db)
    assert user is not None
    assert user["name"] == "Rohan Gupta"
    assert user["email"] == "rohan@example.com"
    assert user["username"] == "rohan10"

    # Case-insensitive retrieval
    by_email = db.get_user_by_email_or_username("ROHAN@EXAMPLE.COM", db_path=temp_db)
    assert by_email is not None
    assert by_email["id"] == user_id


def test_account_lockout_mechanism(temp_db):
    pwd_hash = auth.hash_password("SecurePass@123")
    user_id = db.create_user(
        name="Test Lockout",
        email="lockout@example.com",
        username="lockout_user",
        password_hash=pwd_hash,
        class_level=9,
        board="ICSE",
        db_path=temp_db
    )

    # 4 failed attempts should not lock
    for _ in range(4):
        db.record_login_failure(user_id, max_attempts=5, lock_minutes=15, db_path=temp_db)
        u = db.get_user_by_id(user_id, db_path=temp_db)
        is_locked, remaining = db.check_account_locked(u)
        assert is_locked is False

    # 5th attempt should lock the account
    db.record_login_failure(user_id, max_attempts=5, lock_minutes=15, db_path=temp_db)
    u = db.get_user_by_id(user_id, db_path=temp_db)
    is_locked, remaining = db.check_account_locked(u)
    assert is_locked is True
    assert remaining is not None and remaining >= 1

    # Resetting failures unlocks
    db.reset_login_failures(user_id, db_path=temp_db)
    u = db.get_user_by_id(user_id, db_path=temp_db)
    is_locked, _ = db.check_account_locked(u)
    assert is_locked is False


def test_password_reset_token_expiry_and_single_use(temp_db):
    pwd_hash = auth.hash_password("Pass@1234")
    user_id = db.create_user(
        name="Token User",
        email="token@example.com",
        username="token_user",
        password_hash=pwd_hash,
        class_level=8,
        board="CBSE",
        db_path=temp_db
    )

    raw_token, token_hash = auth.generate_secure_token()

    # Create active reset token (20 mins validity)
    db.create_password_reset_entry(user_id, token_hash, valid_minutes=20, db_path=temp_db)

    # Token should be valid
    entry = db.verify_reset_token_hash(token_hash, db_path=temp_db)
    assert entry is not None
    assert entry["user_id"] == user_id

    # Mark token used -> should not be verifiable again (single use)
    db.mark_reset_token_used(token_hash, db_path=temp_db)
    entry_used = db.verify_reset_token_hash(token_hash, db_path=temp_db)
    assert entry_used is None

    # Test expired token (-5 minutes)
    raw_exp, hash_exp = auth.generate_secure_token()
    db.create_password_reset_entry(user_id, hash_exp, valid_minutes=-5, db_path=temp_db)
    assert db.verify_reset_token_hash(hash_exp, db_path=temp_db) is None


def test_strict_multi_tenant_data_isolation(temp_db):
    # User 1
    u1_id = db.create_user("User One", "user1@example.com", "user1", "hash", 10, "CBSE", db_path=temp_db)
    # User 2
    u2_id = db.create_user("User Two", "user2@example.com", "user2", "hash", 10, "CBSE", db_path=temp_db)

    # User 1 creates a session
    s1_id = "session_user_1"
    db.create_chat_session(s1_id, u1_id, "Algebra Doubt", 10, "CBSE", "Maths", db_path=temp_db)

    # User 2 creates a session
    s2_id = "session_user_2"
    db.create_chat_session(s2_id, u2_id, "Biology Doubt", 10, "CBSE", "Science", db_path=temp_db)

    # User 1 must only see their own sessions
    u1_sessions = db.get_user_chat_sessions(u1_id, db_path=temp_db)
    assert len(u1_sessions) == 1
    assert u1_sessions[0]["id"] == s1_id

    # User 2 cannot access User 1's session
    assert db.get_chat_session(s1_id, user_id=u2_id, db_path=temp_db) is None

    # User 1 cannot delete User 2's session
    deleted = db.delete_chat_session(s2_id, user_id=u1_id, db_path=temp_db)
    assert deleted is False
    assert db.get_chat_session(s2_id, user_id=u2_id, db_path=temp_db) is not None
