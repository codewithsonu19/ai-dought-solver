"""
Profile and Account Settings Page for AI Doubt Solver.
Enables students to update their profile details (Name, Class, Board),
change their password with current password verification, and safely delete their account.
"""

import streamlit as st
import auth
import db
import utils

utils.apply_custom_styles()
auth.init_session_state()

user = auth.require_login()
utils.render_flash_messages()

utils.render_brand_header(
    title="Profile & Settings",
    subtitle=f"Manage your learning account ({user['username']})"
)

tab_profile, tab_security, tab_danger = st.tabs(["👤 Profile Information", "🔐 Change Password", "⚠️ Delete Account"])

# ---------------- TAB 1: PROFILE INFORMATION ---------------- #
with tab_profile:
    st.markdown("### Update Learning Profile")
    
    col1, col2 = st.columns(2)
    with col1:
        updated_name = st.text_input("Full Name", value=user["name"])
        updated_email = st.text_input("Email Address", value=user["email"], disabled=True, help="Email address cannot be changed directly.")
        updated_username = st.text_input("Username", value=user["username"], disabled=True)

    with col2:
        class_idx = max(0, min(11, user["class_level"] - 1))
        updated_class = st.selectbox(
            "Current Class / Grade",
            options=list(range(1, 13)),
            index=class_idx,
            format_func=lambda c: f"Class {c}"
        )

        board_opts = utils.BOARD_OPTIONS
        board_idx = board_opts.index(user["board"]) if user["board"] in board_opts else 0
        updated_board = st.selectbox("Education Board", options=board_opts, index=board_idx)

        updated_guardian = st.text_input("Parent / Guardian Email", value=user.get("guardian_email") or "")

    if st.button("Save Profile Changes", type="primary"):
        if not updated_name or len(updated_name.strip()) < 2:
            st.error("Name must be at least 2 characters.")
        elif updated_guardian and not auth.EMAIL_REGEX.match(updated_guardian.strip()):
            st.error("Please enter a valid guardian email address.")
        else:
            db.update_user_profile(
                user_id=user["id"],
                name=updated_name,
                class_level=updated_class,
                board=updated_board,
                guardian_email=updated_guardian
            )
            # Refresh user in session state
            refreshed = db.get_user_by_id(user["id"])
            auth.set_logged_in_user(refreshed)
            st.success("Profile updated successfully!")
            st.rerun()


# ---------------- TAB 2: CHANGE PASSWORD ---------------- #
with tab_security:
    st.markdown("### Change Your Password")
    st.caption("Keep your account safe by using a strong, unique password.")

    current_pwd = st.text_input("Current Password", type="password", key="chg_curr_pwd")
    new_pwd = st.text_input("New Password", type="password", key="chg_new_pwd")
    confirm_new_pwd = st.text_input("Confirm New Password", type="password", key="chg_conf_pwd")

    if new_pwd:
        st_eval = auth.evaluate_password_strength(new_pwd)
        st.markdown(f"**Strength:** <span style='color:{st_eval['color']}; font-weight:700;'>{st_eval['level']}</span>", unsafe_allow_html=True)
        st.progress(min(1.0, max(0.05, st_eval["score"] / 4.0)))

    if st.button("Update Password", type="primary", key="btn_update_pwd"):
        if not current_pwd or not new_pwd or not confirm_new_pwd:
            st.error("All password fields are required.")
        elif new_pwd != confirm_new_pwd:
            st.error("New password and confirmation do not match.")
        else:
            # Fetch fresh user from DB to verify current password
            fresh_user = db.get_user_by_id(user["id"])
            if not fresh_user or not auth.verify_password(current_pwd, fresh_user["password_hash"]):
                st.error("Current password is incorrect.")
            else:
                strength = auth.evaluate_password_strength(new_pwd)
                if not strength["is_valid"]:
                    st.error(f"New password is too weak. Requirements: {', '.join(strength['missing'])}")
                else:
                    new_hash = auth.hash_password(new_pwd)
                    db.update_user_password(user["id"], new_hash)
                    st.success("Your password has been updated successfully!")


# ---------------- TAB 3: DANGER ZONE ---------------- #
with tab_danger:
    st.markdown("### ⚠️ Delete Account & All Data")
    st.markdown(
        "<div style='color:#dc2626; background:#fee2e2; padding:12px; border-radius:8px;'>"
        "<strong>Warning:</strong> Deleting your account will permanently wipe your profile, "
        "all saved doubts, chat messages, and feedback records. This action cannot be undone."
        "</div>",
        unsafe_allow_html=True
    )
    st.write("")

    confirm_box = st.checkbox("I understand that this action is irreversible and wish to delete my account permanently.")

    if st.button("Permanently Delete My Account", type="primary", disabled=not confirm_box):
        db.delete_user_account(user["id"])
        auth.logout_user()
        st.session_state.flash_message = "Your account and all associated data have been permanently deleted."
        st.session_state.flash_type = "info"
        st.rerun()
