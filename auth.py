"""
Authentication and security functions for AI Doubt Solver.
Includes bcrypt password hashing, input validation, live strength scoring,
secure token generation, session management, and account lockout handling.
"""

import re
import secrets
import hashlib
import datetime
from typing import Tuple, Dict, Any, Optional
import bcrypt
import streamlit as st

import db

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
SPECIAL_CHAR_REGEX = re.compile(r"""[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\/'`]""")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def generate_secure_token() -> Tuple[str, str]:
    """
    Generate a cryptographically secure reset token and its SHA-256 hash.
    Returns (raw_token, token_hash).
    Only the hash is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash


def hash_token(token: str) -> str:
    """Compute SHA-256 digest of a token string."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def evaluate_password_strength(password: str) -> Dict[str, Any]:
    """
    Evaluate password strength against school-secure standards:
    - Min 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    Returns score (0 to 4), level ('Very Weak', 'Weak', 'Medium', 'Strong'), and details.
    """
    length_ok = len(password) >= 8
    upper_ok = bool(re.search(r"[A-Z]", password))
    lower_ok = bool(re.search(r"[a-z]", password))
    digit_ok = bool(re.search(r"[0-9]", password))
    special_ok = bool(SPECIAL_CHAR_REGEX.search(password))

    criteria_met = sum([length_ok, upper_ok, lower_ok, digit_ok, special_ok])
    
    if criteria_met <= 1:
        level = "Very Weak"
        color = "#e63946"
        score = 0
    elif criteria_met <= 3:
        level = "Weak"
        color = "#f4a261"
        score = 1
    elif criteria_met == 4:
        level = "Medium"
        color = "#e9c46a"
        score = 2
    else:
        # criteria_met == 5
        level = "Strong"
        color = "#2a9d8f"
        score = 3
        if len(password) >= 12:
            score = 4
            level = "Very Strong"

    is_valid = (length_ok and upper_ok and lower_ok and digit_ok and special_ok)

    missing = []
    if not length_ok:
        missing.append("At least 8 characters")
    if not upper_ok:
        missing.append("At least 1 uppercase letter (A-Z)")
    if not lower_ok:
        missing.append("At least 1 lowercase letter (a-z)")
    if not digit_ok:
        missing.append("At least 1 number (0-9)")
    if not special_ok:
        missing.append("At least 1 special character (!@#$%^&*...)")

    return {
        "score": score,
        "level": level,
        "color": color,
        "is_valid": is_valid,
        "missing": missing,
        "details": {
            "length": length_ok,
            "uppercase": upper_ok,
            "lowercase": lower_ok,
            "lower": lower_ok,
            "digit": digit_ok,
            "special": special_ok,
        }
    }


def validate_registration_inputs(
    name: str,
    email: str,
    username: str,
    class_level: int,
    board: str,
    password: str,
    confirm_password: str,
    terms_agreed: bool,
    guardian_email: Optional[str] = None,
    db_path: str = db.DB_PATH
) -> Tuple[bool, str]:
    """Validate all registration fields."""
    if not name or len(name.strip()) < 2:
        return False, "Please enter your full name (at least 2 characters)."

    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please enter a valid email address."

    if not username or not USERNAME_REGEX.match(username.strip()):
        return False, "Username must be 3-30 characters with letters, numbers, and underscores only."

    if class_level < 1 or class_level > 12:
        return False, "Please select a valid class between 1 and 12."

    if not board:
        return False, "Please select your education board."

    if guardian_email and not EMAIL_REGEX.match(guardian_email.strip()):
        return False, "Please enter a valid parent/guardian email address."

    if not terms_agreed:
        return False, "You must agree to the Terms of Service & Privacy Policy to create an account."

    if password != confirm_password:
        return False, "Passwords do not match."

    strength = evaluate_password_strength(password)
    if not strength["is_valid"]:
        missing_text = ", ".join(strength["missing"])
        return False, f"Password is not strong enough. Requirements: {missing_text}."

    # Check database uniqueness
    if db.get_user_by_email(email, db_path=db_path):
        return False, "An account with this email address already exists. Please log in or reset your password."

    if db.get_user_by_username(username, db_path=db_path):
        return False, "This username is already taken. Please choose another username."

    return True, ""


def authenticate_user(
    identifier: str,
    password: str,
    max_attempts: int = 5,
    lock_minutes: int = 15,
    db_path: str = db.DB_PATH
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticate a user by email/username and password.
    Enforces account lockout (5 attempts -> 15 min lock).
    Returns (success, user_dict, message).
    """
    if not identifier or not password:
        return False, None, "Please enter both email/username and password."

    user = db.get_user_by_email_or_username(identifier, db_path=db_path)
    if not user:
        # Constant-time mitigation / generic error
        return False, None, "Invalid credentials. Please check your username/email and password."

    # Check if account is locked
    is_locked, remaining_mins = db.check_account_locked(user)
    if is_locked:
        return False, None, f"Account is temporarily locked due to {max_attempts} failed attempts. Please try again in {remaining_mins} minute(s)."

    # Verify password hash
    if not verify_password(password, user["password_hash"]):
        curr_attempts, locked_until = db.record_login_failure(user["id"], max_attempts=max_attempts, lock_minutes=lock_minutes, db_path=db_path)
        if locked_until:
            return False, None, f"Account has been locked for {lock_minutes} minutes after {max_attempts} consecutive failed attempts."
        remaining = max(0, max_attempts - curr_attempts)
        return False, None, f"Invalid credentials. ({remaining} attempt(s) remaining before account lockout)"

    # Login successful: reset failed attempts
    db.reset_login_failures(user["id"], db_path=db_path)
    
    # Return fresh user record
    updated_user = db.get_user_by_id(user["id"], db_path=db_path)
    return True, updated_user, "Login successful!"


# ---------------- SESSION STATE HELPERS ---------------- #

def init_session_state() -> None:
    """Initialize necessary keys in Streamlit session_state."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "last_active" not in st.session_state:
        st.session_state.last_active = datetime.datetime.now(datetime.timezone.utc)
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "active_doubt_session" not in st.session_state:
        st.session_state.active_doubt_session = None
    if "flash_message" not in st.session_state:
        st.session_state.flash_message = None
    if "flash_type" not in st.session_state:
        st.session_state.flash_type = "info"


def check_session_timeout(timeout_minutes: int = 60) -> bool:
    """
    Check if the user's session has timed out due to inactivity.
    If timed out, logs the user out.
    """
    if not st.session_state.get("user"):
        return False

    last_active = st.session_state.get("last_active")
    now = datetime.datetime.now(datetime.timezone.utc)

    if last_active:
        diff_minutes = (now - last_active).total_seconds() / 60.0
        if diff_minutes > timeout_minutes:
            st.session_state.user = None
            st.session_state.current_session_id = None
            st.session_state.flash_message = f"Your session timed out after {timeout_minutes} minutes of inactivity. Please log in again."
            st.session_state.flash_type = "warning"
            return True

    st.session_state.last_active = now
    return False


def set_logged_in_user(user: Dict[str, Any]) -> None:
    """Store the authenticated user in Streamlit session state."""
    # Ensure sensitive password hash is never kept in the session state dictionary
    clean_user = {k: v for k, v in user.items() if k != "password_hash"}
    st.session_state.user = clean_user
    st.session_state.last_active = datetime.datetime.now(datetime.timezone.utc)


def logout_user() -> None:
    """Log out current user and clear session data."""
    st.session_state.user = None
    st.session_state.current_session_id = None
    st.session_state.flash_message = "You have been logged out successfully."
    st.session_state.flash_type = "success"


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the currently logged in user dictionary or None."""
    return st.session_state.get("user")


def require_login():
    """
    Enforce login protection. If not logged in, redirects to Login.
    Returns the user dict if authenticated.
    """
    user = get_current_user()
    if not user:
        st.session_state.flash_message = "Please log in to access this page."
        st.session_state.flash_type = "warning"
        st.rerun()
    return user
