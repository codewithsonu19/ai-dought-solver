"""
History Page for AI Doubt Solver.
Provides full access to past doubt sessions for the authenticated user,
enforcing strict multi-tenant isolation where users can never see another user's doubts.
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
    title="Your Doubt History",
    subtitle=f"Saved learning sessions for {user['name']}"
)

# Fetch user's own sessions only
sessions = db.get_user_chat_sessions(user["id"], limit=100)

if not sessions:
    st.info("You haven't asked any doubts yet! Start by opening the Doubt Solver.")
    if st.button("Go to Doubt Solver", type="primary"):
        st.switch_page("pages/doubt_solver.py")
else:
    # Search and Filter
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_query = st.text_input("🔍 Search past doubts by keyword", placeholder="e.g. Quadratic, Photosynthesis...")
    with col_f2:
        subject_filter = st.selectbox(
            "Filter by Subject",
            options=["All Subjects"] + sorted(list({s["subject"] for s in sessions}))
        )

    filtered_sessions = sessions
    if search_query:
        q = search_query.strip().lower()
        filtered_sessions = [s for s in filtered_sessions if q in s["title"].lower() or q in s["subject"].lower()]
    if subject_filter != "All Subjects":
        filtered_sessions = [s for s in filtered_sessions if s["subject"] == subject_filter]

    st.markdown(f"Found **{len(filtered_sessions)}** saved doubt session(s):")

    for s in filtered_sessions:
        with st.container():
            col_info, col_actions = st.columns([4, 1.2])
            
            with col_info:
                st.markdown(f"### 📘 {s['subject']}: {s['title']}")
                st.markdown(
                    f"<span class='student-badge'>Class {s['class_level']}</span> "
                    f"<span class='student-badge'>{s['board']}</span> "
                    f"<span class='student-badge'>{s['mode']}</span> "
                    f"<span class='student-badge'>{s['language']}</span> "
                    f"<span style='color:#64748b; font-size:0.85rem; margin-left:8px;'>Saved: {s['created_at'][:16]}</span>",
                    unsafe_allow_html=True
                )
            
            with col_actions:
                st.write("") # Spacing
                if st.button("💬 Open Chat", key=f"hist_open_{s['id']}", use_container_width=True, type="primary"):
                    st.session_state.current_session_id = s["id"]
                    st.session_state.active_doubt_session = s
                    st.switch_page("pages/doubt_solver.py")

                if st.button("🗑️ Delete", key=f"hist_del_{s['id']}", use_container_width=True):
                    db.delete_chat_session(s["id"], user["id"])
                    if st.session_state.get("current_session_id") == s["id"]:
                        st.session_state.current_session_id = None
                    st.success("Session deleted.")
                    st.rerun()

            st.markdown("---")
