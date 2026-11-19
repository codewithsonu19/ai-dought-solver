"""
Login Page for AI Doubt Solver.
Features rate-limited authentication, account lockout warnings,
show/hide password toggle, and links to registration and password reset.
"""

import os
import streamlit as st
import auth
import db
import utils

utils.apply_custom_styles()
auth.init_session_state()

# If already logged in, rerun to load student workspace
if auth.get_current_user():
    st.rerun()

utils.render_brand_header(
    title="AI Doubt Solver",
    subtitle="Log in to access your personal grade-adaptive doubt assistant"
)

utils.render_flash_messages()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🔐 Student & Parent Login")
    
    with st.form("login_form", clear_on_submit=False):
        identifier = st.text_input(
            "Email or Username",
            placeholder="e.g. rahul123 or student@example.com",
            help="Enter your registered email address or username."
        )

        show_pwd = st.checkbox("Show password", key="login_show_pwd")
        password = st.text_input(
            "Password",
            type="default" if show_pwd else "password",
            placeholder="Enter your password"
        )

        remember_me = st.checkbox("Remember me on this browser", value=True)

        submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

        if submitted:
            if not identifier or not password:
                st.error("Please enter both email/username and password.")
            else:
                success, user, message = auth.authenticate_user(
                    identifier=identifier,
                    password=password,
                    max_attempts=5,
                    lock_minutes=15
                )

                if success and user:
                    auth.set_logged_in_user(user)
                    st.session_state.flash_message = f"Welcome back, {user['name']}! Ready to solve doubts."
                    st.session_state.flash_type = "success"
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔑 Forgot Password?", use_container_width=True):
            st.switch_page("pages/forgot_password.py")
    with col_b:
        if st.button("📝 Create New Account", use_container_width=True):
            st.switch_page("pages/register.py")

    # DEV MODE HELPER BANNER
    if os.getenv("DEV_MODE", "true").lower() == "true":
        with st.expander("🛠️ Dev Mode: Demo Test Accounts"):
            st.markdown("""
            **Demo Student Account:**
            - Email: `student@example.com` (or username: `demo_student`)
            - Password: `Student@123`
            - Class: 10 | Board: CBSE

            **Demo Admin Account:**
            - Email: `admin@example.com` (or username: `demo_admin`)
            - Password: `Admin@123`
            - Role: Admin
            """)
