"""
Forgot Password Page for AI Doubt Solver.
Implements non-enumerating reset requests, rate limiting (3 requests/hour),
SHA-256 token hashing, single-use expiration, and DEV_MODE UI fallback.
"""

import os
import streamlit as st
import auth
import db
import email_utils
import utils

utils.apply_custom_styles()
auth.init_session_state()

utils.render_brand_header(
    title="Reset Your Password",
    subtitle="We will help you recover access to your learning account"
)

utils.render_flash_messages()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🔑 Request Password Reset")
    st.write("Enter your registered email address below. If an account is associated with this email, you will receive a secure single-use password reset link.")

    email_input = st.text_input("Registered Email Address", placeholder="student@example.com")

    if st.button("Send Reset Link", type="primary", use_container_width=True):
        if not email_input or not auth.EMAIL_REGEX.match(email_input.strip()):
            st.error("Please enter a valid email address.")
        else:
            email_clean = email_input.strip().lower()
            user = db.get_user_by_email(email_clean)

            # Regardless of whether the user exists, we show a constant generic message
            generic_success = "If this email exists in our system, a password reset link has been sent. Please check your inbox and spam folder."

            if user:
                # Check rate limiting: max 3 per hour
                max_resets = int(os.getenv("MAX_RESET_REQUESTS_PER_HOUR", "3"))
                recent_count = db.count_recent_reset_requests(user["id"], window_hours=1)

                if recent_count >= max_resets:
                    st.warning(f"Too many reset requests. For your security, you can only request {max_resets} reset links per hour. Please wait before trying again.")
                else:
                    # Generate token and store ONLY its hash
                    raw_token, token_hash = auth.generate_secure_token()
                    db.create_password_reset_entry(
                        user_id=user["id"],
                        token_hash=token_hash,
                        valid_minutes=20
                    )

                    # Send email (or console fallback)
                    success, status_msg, reset_link = email_utils.send_password_reset_email(
                        to_email=user["email"],
                        username=user["username"],
                        raw_token=raw_token,
                        valid_minutes=20
                    )

                    st.success(generic_success)

                    # DEV_MODE assistance banner for instant verification
                    if email_utils.is_dev_mode():
                        st.info("🛠️ **DEV MODE ACTIVE:** Since you are testing locally, here is your generated reset link and token:")
                        st.code(f"Reset Link: {reset_link}\nReset Token: {raw_token}")
                        if st.button("👉 Proceed to Reset Password Now"):
                            st.session_state["dev_prefill_token"] = raw_token
                            st.switch_page("pages/reset_password.py")
            else:
                # Security: Never leak non-existence of email
                st.success(generic_success)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⬅️ Back to Login", use_container_width=True):
            st.switch_page("pages/login.py")
    with col_b:
        if st.button("Enter Reset Code", use_container_width=True):
            st.switch_page("pages/reset_password.py")
