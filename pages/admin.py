"""
Admin Metrics Dashboard for AI Doubt Solver.
Provides high-level insights into user registrations, active sessions,
feedback ratings, and grade distribution. Only accessible to users with the 'admin' role.
"""

import streamlit as st
import auth
import db
import utils

utils.apply_custom_styles()
auth.init_session_state()

user = auth.require_login()

if user.get("role") != "admin":
    st.error("Access Denied: You do not have administrator privileges.")
    if st.button("Return to Doubt Solver"):
        st.switch_page("pages/doubt_solver.py")
    st.stop()

utils.render_brand_header(
    title="Admin Analytics Dashboard",
    subtitle="AI Doubt Solver System Performance & Student Feedback"
)

metrics = db.get_admin_metrics()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", metrics["total_users"])
col2.metric("Chat Sessions", metrics["total_sessions"])
col3.metric("Messages Exchanged", metrics["total_messages"])

total_fb = metrics["thumbs_up"] + metrics["thumbs_down"]
up_pct = int((metrics["thumbs_up"] / total_fb * 100)) if total_fb > 0 else 100
col4.metric("Student Satisfaction", f"{up_pct}%", f"👍 {metrics['thumbs_up']} | 👎 {metrics['thumbs_down']}")

st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📊 Class Distribution")
    if metrics["class_distribution"]:
        for item in metrics["class_distribution"]:
            st.write(f"**Class {item['class_level']}**: {item['count']} student(s)")
    else:
        st.write("No data yet.")

with col_b:
    st.subheader("🏫 Board Distribution")
    if metrics["board_distribution"]:
        for item in metrics["board_distribution"]:
            st.write(f"**{item['board']}**: {item['count']} student(s)")
    else:
        st.write("No data yet.")

st.markdown("---")
if st.button("Back to Doubt Solver"):
    st.switch_page("pages/doubt_solver.py")
