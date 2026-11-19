"""
Comprehensive end-to-end smoke test script for AI Doubt Solver.
Tests all modules, database operations, auth operations, LLM prompts,
and simulated student doubt solving workflows.
"""

import os
import sys
from PIL import Image

def run_tests():
    print("=" * 60)
    print("1. Testing Database & Schema Initialization...")
    import db
    db.init_db()
    db.seed_demo_users()
    print("   [OK] Database initialized and demo accounts seeded.")

    print("\n2. Testing Demo Accounts Retrieval...")
    student = db.get_user_by_email("student@example.com")
    admin = db.get_user_by_email("admin@example.com")
    assert student is not None, "Demo student not found!"
    assert admin is not None, "Demo admin not found!"
    print(f"   [OK] Found student: {student['name']} (Class {student['class_level']} {student['board']})")
    print(f"   [OK] Found admin: {admin['name']} (Role: {admin['role']})")

    print("\n3. Testing Auth & Password Verification...")
    import auth
    assert auth.verify_password("Student@123", student["password_hash"]), "Student password verify failed!"
    assert auth.verify_password("Admin@123", admin["password_hash"]), "Admin password verify failed!"
    
    # Test wrong password fails
    assert not auth.verify_password("WrongPassword!", student["password_hash"]), "Wrong password should fail!"
    print("   [OK] Passwords hashed with bcrypt and verified successfully.")

    print("\n4. Testing Live Password Strength Evaluator...")
    weak = auth.evaluate_password_strength("weak")
    assert not weak["is_valid"], "Weak password should not be valid"
    strong = auth.evaluate_password_strength("SuperSecret@2026")
    assert strong["is_valid"], "Strong password should be valid"
    assert "lower" in strong["details"] and "lowercase" in strong["details"]
    print("   [OK] Password strength scoring and detail keys verified.")

    print("\n5. Testing Account Lockout Logic...")
    test_user_id = db.create_user(
        name="Lockout Test",
        email="test_lockout@example.com",
        username="test_lockout_user",
        password_hash=auth.hash_password("Pass@1234"),
        class_level=8,
        board="CBSE"
    )
    for _ in range(5):
        db.record_login_failure(test_user_id, max_attempts=5, lock_minutes=15)
    locked_user = db.get_user_by_id(test_user_id)
    is_locked, remaining = db.check_account_locked(locked_user)
    assert is_locked, "Account should be locked after 5 failed attempts!"
    print(f"   [OK] Account correctly locked for {remaining} minutes after 5 failures.")
    db.reset_login_failures(test_user_id)
    unlocked_user = db.get_user_by_id(test_user_id)
    is_locked_now, _ = db.check_account_locked(unlocked_user)
    assert not is_locked_now, "Account should be unlocked after reset!"
    print("   [OK] Account correctly unlocked after reset.")
    db.delete_user_account(test_user_id)

    print("\n6. Testing Reset Token Generation & Expiration...")
    raw_token, token_hash = auth.generate_secure_token()
    db.create_password_reset_entry(student["id"], token_hash, valid_minutes=20)
    entry = db.verify_reset_token_hash(token_hash)
    assert entry is not None, "Token should be valid!"
    db.mark_reset_token_used(token_hash)
    assert db.verify_reset_token_hash(token_hash) is None, "Token must be single-use!"
    print("   [OK] Reset token single-use and hash verification passed.")

    print("\n7. Testing Multi-Tenant Doubt Sessions & Messages...")
    session_id = "test_smoke_session_01"
    db.create_chat_session(
        session_id=session_id,
        user_id=student["id"],
        title="Quadratic Formula Doubt",
        class_level=10,
        board="CBSE",
        subject="Maths",
        language="English",
        mode="Step-by-Step"
    )
    m1_id = db.add_message(session_id, "user", "How do I solve 2x^2 - 4x + 1 = 0?")
    m2_id = db.add_message(session_id, "assistant", "### 1. Understanding\nWe need to solve the quadratic equation.")
    db.save_feedback(m2_id, student["id"], rating=1, comments="Great explanation!")
    
    # Verify retrieval
    msgs = db.get_session_messages(session_id)
    assert len(msgs) == 2, f"Expected 2 messages, got {len(msgs)}"
    rating = db.get_feedback_for_message(m2_id, student["id"])
    assert rating == 1, f"Expected rating 1, got {rating}"
    print(f"   [OK] Chat session created, messages stored, and feedback (+1) recorded.")

    # Isolation check: Admin cannot access student's session
    admin_session_check = db.get_chat_session(session_id, user_id=admin["id"])
    assert admin_session_check is None, "Data isolation breach: Admin accessed student session!"
    print("   [OK] Multi-tenant isolation verified (admin cannot see student session).")
    
    # Clean up test session
    db.delete_chat_session(session_id, student["id"])

    print("\n8. Testing LLM Response Generation (Grades 2, 8, 12, Image)...")
    import llm
    # Class 2 Maths
    ok1, r1 = llm.generate_doubt_solution("5 + 3", 2, "CBSE", "Maths")
    assert ok1 and "Final Answer" in r1, "Class 2 response failed!"
    print("   [OK] Class 2 Primary Grade explanation generated.")

    # Class 8 Science
    ok2, r2 = llm.generate_doubt_solution("What is combustion?", 8, "CBSE", "Science")
    assert ok2 and "Common Mistake to Avoid" in r2, "Class 8 response failed!"
    print("   [OK] Class 8 Middle Grade explanation generated.")

    # Class 12 Physics
    ok3, r3 = llm.generate_doubt_solution("Derive electric field due to dipole", 12, "CBSE", "Physics")
    assert ok3 and "Key Concept" in r3, "Class 12 Senior Grade response failed!"
    print("   [OK] Class 12 Senior Grade explanation generated.")

    # Multimodal Image
    test_img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    ok4, r4 = llm.generate_doubt_solution("Solve this problem", 10, "CBSE", "Maths", image=test_img)
    assert ok4 and "Practice Questions" in r4, "Multimodal response failed!"
    print("   [OK] Multimodal Image-based doubt resolved.")

    print("\n9. Testing Utilities & Subject Mappings...")
    import utils
    assert "EVS" in utils.get_subjects_for_class(3), "Class 3 should have EVS"
    assert "Physics" in utils.get_subjects_for_class(11), "Class 11 should have Physics"
    assert "Science" in utils.get_subjects_for_class(9), "Class 9 should have Science"
    print("   [OK] Subject mappings dynamically aligned to classes.")

    print("\n" + "=" * 60)
    print("🎉 ALL 9 CRITICAL SUBSYSTEM TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
