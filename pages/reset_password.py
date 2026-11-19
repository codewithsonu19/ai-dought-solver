"""
Reset Password Page for AI Doubt Solver.
Validates single-use cryptographic tokens, checks expiration,
enforces password strength, updates password hash, and marks tokens used.
"""

import streamlit as st
import auth
import db
import utils

utils.apply_custom_styles()
auth.init_session_state()

utils.render_brand_header(
    title="Choose a New Password",
    subtitle="Secure your AI Doubt Solver learning account"
)

utils.render_flash_messages()

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🔒 Set New Password")

    # Read token from query parameters or session prefill
    query_token = st.query_params.get("token", "")
    dev_token = st.session_state.pop("dev_prefill_token", "")
    initial_token = query_token or dev_token

    token_input = st.text_input(
        "Reset Token / Code",
        value=initial_token,
        placeholder="Paste your reset token here",
        help="Paste the single-use token sent to your email."
    )

    show_pwd = st.checkbox("Show passwords", key="reset_show_pwd")
    pwd_type = "default" if show_pwd else "password"

    new_password = st.text_input(
        "New Password",
        type=pwd_type,
        placeholder="Enter a new strong password",
        key="reset_new_pwd"
    )

    confirm_new_password = st.text_input(
        "Confirm New Password",
        type=pwd_type,
        placeholder="Re-enter your new password",
        key="reset_confirm_pwd"
    )

    # Live strength meter
    if new_password:
        strength = auth.evaluate_password_strength(new_password)
        st.markdown(
            f"**Password Strength:** <span style='color:{strength['color']}; font-weight:700;'>{strength['level']}</span>",
            unsafe_allow_html=True
        )
        progress_val = min(1.0, max(0.05, strength["score"] / 4.0))
        st.progress(progress_val)
        det = strength["details"]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown("✅ 8+" if det.get("length") else "❌ 8+")
        c2.markdown("✅ A-Z" if det.get("uppercase") else "❌ A-Z")
        c3.markdown("✅ a-z" if det.get("lowercase") or det.get("lower") else "❌ a-z")
        c4.markdown("✅ 0-9" if det.get("digit") else "❌ 0-9")
        c5.markdown("✅ Special" if det.get("special") else "❌ Special")

    if st.button("Update Password", type="primary", use_container_width=True):
        if not token_input:
            st.error("Please provide your reset token.")
        elif not new_password or not confirm_new_password:
            st.error("Please fill in both password fields.")
        elif new_password != confirm_new_password:
            st.error("New password and confirm password do not match.")
        else:
            strength = auth.evaluate_password_strength(new_password)
            if not strength["is_valid"]:
                missing_text = ", ".join(strength["missing"])
                st.error(f"Password does not meet security criteria: {missing_text}.")
            else:
                # Hash token and verify in database
                token_hash = auth.hash_token(token_input)
                reset_entry = db.verify_reset_token_hash(token_hash)

                if not reset_entry:
                    st.error("This reset token is invalid, already used, or has expired. Please request a new reset link.")
                else:
                    # Token is valid: update user's password with new bcrypt hash
                    new_hash = auth.hash_password(new_password)
                    db.update_user_password(reset_entry["user_id"], new_hash)

                    # Mark token as used (single use enforcement)
                    db.mark_reset_token_used(token_hash)

                    # Invalidate any active session
                    auth.logout_user()

                    st.session_state.flash_message = "Your password has been successfully reset! Please log in with your new password."
                    st.session_state.flash_type = "success"
                    st.switch_page("pages/login.py")

    st.markdown("---")
    if st.button("⬅️ Back to Login", use_container_width=True):
        st.switch_page("pages/login.py")
