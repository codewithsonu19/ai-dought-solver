"""
Database layer for AI Doubt Solver.
Uses SQLite with strictly parameterized queries to prevent SQL injection.
Handles users, password resets, chat sessions, messages, and feedback.
"""

import os
import sqlite3
import datetime
from typing import Optional, Dict, Any, List, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doubt_solver.db")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize database tables and indexes."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                board TEXT NOT NULL,
                guardian_email TEXT,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Password Resets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Chat Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                class_level INTEGER NOT NULL,
                board TEXT NOT NULL,
                subject TEXT NOT NULL,
                language TEXT DEFAULT 'English',
                mode TEXT DEFAULT 'Step-by-Step',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
            )
        """)

        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL, -- 1 for up, -1 for down
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resets_token_hash ON password_resets(token_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_msg ON feedback(message_id)")

        conn.commit()


def seed_demo_users(db_path: str = DB_PATH) -> None:
    """Seed demo student and admin accounts when DEV_MODE is enabled."""
    import auth
    
    # 1. Seed demo student if not present
    student = get_user_by_email("student@example.com", db_path=db_path)
    if not student:
        demo_pwd_hash = auth.hash_password("Student@123")
        create_user(
            name="Aarav Sharma (Demo)",
            email="student@example.com",
            username="demo_student",
            password_hash=demo_pwd_hash,
            class_level=10,
            board="CBSE",
            guardian_email="guardian@example.com",
            role="student",
            db_path=db_path
        )

    # 2. Seed demo admin if not present
    admin = get_user_by_email("admin@example.com", db_path=db_path)
    if not admin:
        admin_pwd_hash = auth.hash_password("Admin@123")
        create_user(
            name="Teacher Admin",
            email="admin@example.com",
            username="demo_admin",
            password_hash=admin_pwd_hash,
            class_level=12,
            board="CBSE",
            guardian_email=None,
            role="admin",
            db_path=db_path
        )



# ---------------- USER FUNCTIONS ---------------- #

def create_user(
    name: str,
    email: str,
    username: str,
    password_hash: str,
    class_level: int,
    board: str,
    guardian_email: Optional[str] = None,
    role: str = "student",
    db_path: str = DB_PATH
) -> int:
    """Create a new user. Returns the user id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, username, password_hash, class_level, board, guardian_email, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name.strip(),
            email.strip().lower(),
            username.strip().lower(),
            password_hash,
            class_level,
            board.strip(),
            guardian_email.strip().lower() if guardian_email else None,
            role
        ))
        conn.commit()
        return cursor.lastrowid


def get_user_by_id(user_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch user by primary key ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email_or_username(identifier: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch user by case-insensitive email or username."""
    identifier_clean = identifier.strip().lower()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email = ? OR username = ?",
            (identifier_clean, identifier_clean)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch user by case-insensitive email."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_username(username: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch user by case-insensitive username."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user_profile(
    user_id: int,
    name: str,
    class_level: int,
    board: str,
    guardian_email: Optional[str] = None,
    db_path: str = DB_PATH
) -> bool:
    """Update profile information of user."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET name = ?, class_level = ?, board = ?, guardian_email = ?
            WHERE id = ?
        """, (
            name.strip(),
            class_level,
            board.strip(),
            guardian_email.strip().lower() if guardian_email else None,
            user_id
        ))
        conn.commit()
        return cursor.rowcount > 0


def update_user_password(user_id: int, new_password_hash: str, db_path: str = DB_PATH) -> bool:
    """Update password hash and reset failed attempts."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, failed_attempts = 0, locked_until = NULL
            WHERE id = ?
        """, (new_password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_user_account(user_id: int, db_path: str = DB_PATH) -> bool:
    """Permanently delete user account and cascade delete all associated data."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


# ---------------- LOCKOUT & SECURITY ---------------- #

def record_login_failure(user_id: int, max_attempts: int = 5, lock_minutes: int = 15, db_path: str = DB_PATH) -> Tuple[int, Optional[str]]:
    """
    Increment failed login attempts. If failed_attempts reaches max_attempts,
    lock the account for lock_minutes.
    Returns (current_attempts, locked_until_iso_or_none).
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT failed_attempts FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        current_attempts = (row["failed_attempts"] if row else 0) + 1

        locked_until_str = None
        if current_attempts >= max_attempts:
            locked_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=lock_minutes)
            locked_until_str = locked_until.isoformat()
            cursor.execute(
                "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                (current_attempts, locked_until_str, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET failed_attempts = ? WHERE id = ?",
                (current_attempts, user_id)
            )
        conn.commit()
        return current_attempts, locked_until_str


def reset_login_failures(user_id: int, db_path: str = DB_PATH) -> None:
    """Reset failed attempts and unlock account upon successful login."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user_id,))
        conn.commit()


def check_account_locked(user: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
    """
    Check if the user account is currently locked.
    Returns (is_locked, remaining_minutes).
    """
    locked_until_raw = user.get("locked_until")
    if not locked_until_raw:
        return False, None

    try:
        # Handle ISO format
        if isinstance(locked_until_raw, str):
            # Strip Z or normalize
            dt_str = locked_until_raw.replace("Z", "+00:00")
            locked_until = datetime.datetime.fromisoformat(dt_str)
        else:
            locked_until = locked_until_raw

        # Ensure timezone-aware comparison
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=datetime.timezone.utc)

        now = datetime.datetime.now(datetime.timezone.utc)
        if now < locked_until:
            remaining_secs = int((locked_until - now).total_seconds())
            remaining_mins = max(1, (remaining_secs + 59) // 60)
            return True, remaining_mins
        return False, None
    except Exception:
        return False, None


# ---------------- PASSWORD RESET TOKENS ---------------- #

def count_recent_reset_requests(user_id: int, window_hours: int = 1, db_path: str = DB_PATH) -> int:
    """Count reset requests made within the last window_hours for rate limiting."""
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=window_hours)).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM password_resets
            WHERE user_id = ? AND created_at >= ?
        """, (user_id, cutoff))
        row = cursor.fetchone()
        return row["cnt"] if row else 0


def create_password_reset_entry(
    user_id: int,
    token_hash: str,
    valid_minutes: int = 20,
    db_path: str = DB_PATH
) -> int:
    """Record a hashed password reset token with expiration."""
    expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=valid_minutes)).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO password_resets (user_id, token_hash, expires_at, used)
            VALUES (?, ?, ?, 0)
        """, (user_id, token_hash, expires_at))
        conn.commit()
        return cursor.lastrowid


def verify_reset_token_hash(token_hash: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """
    Validate the reset token hash.
    Must exist, not be used, and not be expired.
    Returns dict with reset entry and user info, or None.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, u.email, u.username
            FROM password_resets r
            JOIN users u ON r.user_id = u.id
            WHERE r.token_hash = ? AND r.used = 0
            ORDER BY r.id DESC LIMIT 1
        """, (token_hash,))
        row = cursor.fetchone()
        if not row:
            return None

        entry = dict(row)
        expires_at_raw = entry["expires_at"]
        dt_str = expires_at_raw.replace("Z", "+00:00")
        expires_at = datetime.datetime.fromisoformat(dt_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)

        now = datetime.datetime.now(datetime.timezone.utc)
        if now > expires_at:
            return None  # Expired

        return entry


def mark_reset_token_used(token_hash: str, db_path: str = DB_PATH) -> None:
    """Mark a reset token as used (single-use enforcement)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE password_resets SET used = 1 WHERE token_hash = ?", (token_hash,))
        conn.commit()


# ---------------- CHAT SESSIONS & MESSAGES ---------------- #

def create_chat_session(
    session_id: str,
    user_id: int,
    title: str,
    class_level: int,
    board: str,
    subject: str,
    language: str = "English",
    mode: str = "Step-by-Step",
    db_path: str = DB_PATH
) -> str:
    """Create a new chat session for a user."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_sessions (id, user_id, title, class_level, board, subject, language, mode, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, title[:80], class_level, board, subject, language, mode, now_iso, now_iso))
        conn.commit()
        return session_id


def get_user_chat_sessions(user_id: int, limit: int = 50, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve chat sessions strictly owned by the specified user (user data isolation)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_chat_session(session_id: str, user_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single chat session ensuring user owns it."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_sessions
            WHERE id = ? AND user_id = ?
        """, (session_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_chat_session_timestamp(session_id: str, db_path: str = DB_PATH) -> None:
    """Touch the updated_at timestamp of a chat session."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now_iso, session_id))
        conn.commit()


def delete_chat_session(session_id: str, user_id: int, db_path: str = DB_PATH) -> bool:
    """Delete a chat session strictly belonging to user."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def add_message(
    session_id: str,
    role: str,
    content: str,
    image_path: Optional[str] = None,
    db_path: str = DB_PATH
) -> int:
    """Add a message to a session and update session's updated_at."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, image_path)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, image_path))
        msg_id = cursor.lastrowid
        conn.commit()

    update_chat_session_timestamp(session_id, db_path=db_path)
    return msg_id


def get_session_messages(session_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Fetch all messages for a session in chronological order."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, f.rating as user_rating
            FROM messages m
            LEFT JOIN feedback f ON m.id = f.message_id
            WHERE m.session_id = ?
            ORDER BY m.id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


# ---------------- FEEDBACK ---------------- #

def save_feedback(message_id: int, user_id: int, rating: int, comments: Optional[str] = None, db_path: str = DB_PATH) -> int:
    """Save or update feedback rating (+1 or -1) for a message."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Remove previous feedback from this user on this message if any
        cursor.execute("DELETE FROM feedback WHERE message_id = ? AND user_id = ?", (message_id, user_id))
        cursor.execute("""
            INSERT INTO feedback (message_id, user_id, rating, comments)
            VALUES (?, ?, ?, ?)
        """, (message_id, user_id, rating, comments))
        conn.commit()
        return cursor.lastrowid


def get_feedback_for_message(message_id: int, user_id: int, db_path: str = DB_PATH) -> Optional[int]:
    """Get user's rating for a message (+1, -1, or None)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM feedback WHERE message_id = ? AND user_id = ?", (message_id, user_id))
        row = cursor.fetchone()
        return row["rating"] if row else None


# ---------------- ADMIN METRICS ---------------- #

def get_admin_metrics(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieve system stats for admin dashboard."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM chat_sessions")
        total_sessions = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM messages")
        total_messages = cursor.fetchone()["count"]

        cursor.execute("SELECT SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up, SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down FROM feedback")
        fb_row = cursor.fetchone()
        thumbs_up = fb_row["thumbs_up"] or 0
        thumbs_down = fb_row["thumbs_down"] or 0

        cursor.execute("""
            SELECT class_level, COUNT(*) as count
            FROM users
            GROUP BY class_level
            ORDER BY class_level
        """)
        class_dist = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT board, COUNT(*) as count
            FROM users
            GROUP BY board
            ORDER BY count DESC
        """)
        board_dist = [dict(r) for r in cursor.fetchall()]

        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "class_distribution": class_dist,
            "board_distribution": board_dist,
        }
