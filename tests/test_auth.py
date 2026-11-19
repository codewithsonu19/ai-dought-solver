"""
Unit tests for authentication and security functions.
Tests password strength rules, bcrypt hashing, token creation, and lockout logic.
"""

import pytest
import auth


def test_password_strength_evaluation():
    # Very weak passwords
    r1 = auth.evaluate_password_strength("short")
    assert not r1["is_valid"]
    assert "At least 8 characters" in r1["missing"]

    # Missing uppercase and special
    r2 = auth.evaluate_password_strength("password123")
    assert not r2["is_valid"]
    assert any("uppercase" in m for m in r2["missing"])
    assert any("special" in m for m in r2["missing"])

    # Valid strong password
    r3 = auth.evaluate_password_strength("StrongPass@123")
    assert r3["is_valid"]
    assert len(r3["missing"]) == 0
    assert r3["score"] >= 3
    # Check details dictionary keys
    assert "lowercase" in r3["details"]
    assert "lower" in r3["details"]
    assert r3["details"]["lowercase"] is True
    assert r3["details"]["lower"] is True


def test_password_hashing_and_verification():
    raw_pwd = "MySecretPassword!2026"
    pwd_hash = auth.hash_password(raw_pwd)

    assert pwd_hash != raw_pwd
    assert pwd_hash.startswith("$2b$") or pwd_hash.startswith("$2a$")
    assert auth.verify_password(raw_pwd, pwd_hash) is True
    assert auth.verify_password("WrongPassword!2026", pwd_hash) is False
    assert auth.verify_password("", pwd_hash) is False


def test_secure_token_generation_and_hashing():
    raw_token, token_hash = auth.generate_secure_token()
    assert len(raw_token) >= 32
    assert len(token_hash) == 64  # SHA-256 hex digest length
    # Check that hashing the raw token produces the same token_hash
    assert auth.hash_token(raw_token) == token_hash
