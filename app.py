"""
AI Doubt Solver - Main Application Entrypoint.
Initializes database, configures navigation and access control,
manages user session lifetimes, and routes to appropriate views.
"""

import os
import sys
from dotenv import load_dotenv
import streamlit as st

# Enable direct execution from Python IDLE / standard python
if not st.runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", os.path.abspath(__file__), "--server.headless=false"]
    sys.exit(stcli.main())

# Load environment variables early
load_dotenv()

import db
import auth
import utils

# Configure Streamlit page defaults
st.set_page_config(
    page_title="AI Doubt Solver",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema
db.init_db()

# Seed test accounts if DEV_MODE is enabled
if os.getenv("DEV_MODE", "true").lower() == "true":
    db.seed_demo_users()

# Initialize session state tracking
auth.init_session_state()

# Inject global styling
utils.apply_custom_styles()

# Check for reset token in query parameters
query_params = st.query_params
has_reset_token = "token" in query_params or query_params.get("page") == "reset"

current_user = auth.get_current_user()

# Route setup based on login state
if current_user:
    # Authenticated user pages
    user_pages = [
        st.Page("pages/doubt_solver.py", title="Doubt Solver", icon="🎓", default=True),
        st.Page("pages/history.py", title="Doubt History", icon="📚"),
        st.Page("pages/profile.py", title="Profile & Settings", icon="⚙️"),
    ]

    # Add admin dashboard if role is admin
    if current_user.get("role") == "admin":
        user_pages.append(st.Page("pages/admin.py", title="Admin Dashboard", icon="📊"))

    pg = st.navigation(user_pages)
else:
    # Public unauthenticated pages
    is_reset_default = has_reset_token
    public_pages = [
        st.Page("pages/login.py", title="Log In", icon="🔐", default=(not is_reset_default)),
        st.Page("pages/register.py", title="Register", icon="📝"),
        st.Page("pages/forgot_password.py", title="Forgot Password", icon="🔑"),
        st.Page("pages/reset_password.py", title="Reset Password", icon="🔒", default=is_reset_default),
    ]
    pg = st.navigation(public_pages)

pg.run()
