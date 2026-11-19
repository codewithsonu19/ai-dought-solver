"""
Registration Page for AI Doubt Solver.
Collects student details, curriculum board, grade level, and enforces
strict bcrypt-hashed password security with a live strength indicator.
"""

import streamlit as st
import auth
import db
import utils

utils.apply_custom_styles()
auth.init_session_state()

utils.render_brand_header(
    title="Create Your Account",
    subtitle="Join thousands of school students getting instant doubt solutions"
)

utils.render_flash_messages()

col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    st.markdown("### 📝 Student Registration")

    # Outside the form text input for live password strength checking
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        full_name = st.text_input("Full Name *", placeholder="e.g. Aarav Sharma")
        email = st.text_input("Email Address *", placeholder="student@example.com")
        username = st.text_input("Choose Username *", placeholder="e.g. aarav_cbse")
    
    with col_l2:
        class_level = st.selectbox(
            "Select Class / Grade *",
            options=list(range(1, 13)),
            index=9, # Default to Class 10
            format_func=lambda c: f"Class {c}"
        )
        board = st.selectbox("Education Board *", options=utils.BOARD_OPTIONS)
        guardian_email = st.text_input(
            "Parent / Guardian Email (Optional)",
            placeholder="parent@example.com",
            help="Recommended for students under 13 (Classes 1–7) for progress updates and security."
        )

    st.markdown("#### 🔒 Security & Password")

    show_pwd = st.checkbox("Show password", key="reg_show_pwd")
    pwd_type = "default" if show_pwd else "password"

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        password = st.text_input(
            "Password *",
            type=pwd_type,
            placeholder="Min 8 chars, Aa1@...",
            key="reg_password_input",
            help="Must include 8+ chars, uppercase, lowercase, number, and special character."
        )
    with col_p2:
        confirm_password = st.text_input(
            "Confirm Password *",
            type=pwd_type,
            placeholder="Re-enter password",
            key="reg_confirm_password"
        )

    # Live Password Strength Meter
    if password:
        strength = auth.evaluate_password_strength(password)
        st.markdown(
            f"**Password Strength:** <span style='color:{strength['color']}; font-weight:700;'>{strength['level']}</span>",
            unsafe_allow_html=True
        )
        progress_val = min(1.0, max(0.05, strength["score"] / 4.0))
        st.progress(progress_val)

        # Detailed breakdown of requirements
        det = strength["details"]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown("✅ 8+ Chars" if det.get("length") else "❌ 8+ Chars")
        c2.markdown("✅ A-Z" if det.get("uppercase") else "❌ A-Z")
        c3.markdown("✅ a-z" if det.get("lowercase") or det.get("lower") else "❌ a-z")
        c4.markdown("✅ 0-9" if det.get("digit") else "❌ 0-9")
        c5.markdown("✅ Special" if det.get("special") else "❌ Special")

    terms = st.checkbox("I agree to the Terms of Service & Privacy Policy *", value=False)

    if st.button("🚀 Complete Registration", type="primary", use_container_width=True):
        is_valid, err_msg = auth.validate_registration_inputs(
            name=full_name,
            email=email,
            username=username,
            class_level=class_level,
            board=board,
            password=password,
            confirm_password=confirm_password,
            terms_agreed=terms,
            guardian_email=guardian_email
        )

        if not is_valid:
            st.error(err_msg)
        else:
            pwd_hash = auth.hash_password(password)
            try:
                user_id = db.create_user(
                    name=full_name,
                    email=email,
                    username=username,
                    password_hash=pwd_hash,
                    class_level=class_level,
                    board=board,
                    guardian_email=guardian_email,
                    role="student"
                )
                st.session_state.flash_message = "Registration successful! You can now log in with your credentials."
                st.session_state.flash_type = "success"
                st.switch_page("pages/login.py")
            except Exception as e:
                st.error(f"Registration failed: {str(e)}")

    st.markdown("---")
    col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
    with col_back2:
        if st.button("Already have an account? Log In", use_container_width=True):
            st.switch_page("pages/login.py")
