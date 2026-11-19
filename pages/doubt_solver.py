"""
Core Doubt Solver Page for AI Doubt Solver.
Provides grade-adaptive multi-turn AI assistance, textbook/handwritten photo upload,
follow-up conversations, LaTeX math rendering, and per-response feedback (👍 / 👎).
"""

import os
import uuid
import streamlit as st
import auth
import db
import llm
import utils

utils.apply_custom_styles()
auth.init_session_state()

# Session timeout check
if auth.check_session_timeout(timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))):
    st.rerun()

# Enforce authentication
user = auth.require_login()

utils.render_flash_messages()

# ---------------- SIDEBAR CONFIGURATION ---------------- #
with st.sidebar:
    st.markdown(f"### 👤 Student: **{user['name']}**")
    st.caption(f"Registered: Class {user['class_level']} ({user['board']})")

    st.markdown("---")
    st.markdown("### ⚙️ Solver Settings")

    # Pre-fill class and board from profile
    default_class_idx = max(0, min(11, user["class_level"] - 1))
    selected_class = st.selectbox(
        "Current Class / Grade",
        options=list(range(1, 13)),
        index=default_class_idx,
        format_func=lambda c: f"Class {c}",
        key="solver_class_select"
    )

    board_options = utils.BOARD_OPTIONS
    default_board_idx = board_options.index(user["board"]) if user["board"] in board_options else 0
    selected_board = st.selectbox(
        "Education Board",
        options=board_options,
        index=default_board_idx,
        key="solver_board_select"
    )

    # Dynamic subjects based on selected class
    available_subjects = utils.get_subjects_for_class(selected_class)
    selected_subject = st.selectbox(
        "Subject",
        options=available_subjects,
        key="solver_subject_select"
    )

    selected_language = st.selectbox(
        "Answer Language",
        options=utils.LANGUAGE_OPTIONS,
        index=0,
        key="solver_lang_select"
    )

    selected_mode = st.selectbox(
        "Explanation Mode",
        options=utils.EXPLANATION_MODES,
        index=0,
        key="solver_mode_select"
    )

    st.markdown("---")

    # Start new chat button
    if st.button("➕ Start New Doubt", use_container_width=True, type="primary"):
        st.session_state.current_session_id = None
        st.session_state.active_doubt_session = None
        st.rerun()

    # Past Sessions List
    st.markdown("### 📚 Your Past Doubts")
    past_sessions = db.get_user_chat_sessions(user["id"], limit=20)

    if not past_sessions:
        st.caption("No past doubts yet. Ask your first question!")
    else:
        for s in past_sessions:
            col_s1, col_s2 = st.columns([4, 1])
            is_active = (st.session_state.get("current_session_id") == s["id"])
            title_label = f"{'👉 ' if is_active else ''}{s['subject']}: {s['title'][:25]}"
            
            with col_s1:
                if st.button(title_label, key=f"session_btn_{s['id']}", use_container_width=True):
                    st.session_state.current_session_id = s["id"]
                    st.session_state.active_doubt_session = s
                    st.rerun()
            with col_s2:
                if st.button("🗑️", key=f"del_btn_{s['id']}", help="Delete this session"):
                    db.delete_chat_session(s["id"], user["id"])
                    if st.session_state.get("current_session_id") == s["id"]:
                        st.session_state.current_session_id = None
                        st.session_state.active_doubt_session = None
                    st.rerun()

    st.markdown("---")
    if st.button("🚪 Log Out", use_container_width=True):
        auth.logout_user()
        st.rerun()


# ---------------- MAIN CHAT WORKSPACE ---------------- #

# Header Badges
st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:8px;">
    <div>
        <span class="student-badge">Class {selected_class}</span>
        <span class="student-badge">{selected_board}</span>
        <span class="student-badge">{selected_subject}</span>
        <span class="student-badge">Mode: {selected_mode}</span>
        <span class="student-badge">Lang: {selected_language}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Determine active session
current_session_id = st.session_state.get("current_session_id")
messages = []

if current_session_id:
    session_data = db.get_chat_session(current_session_id, user["id"])
    if session_data:
        messages = db.get_session_messages(current_session_id)
    else:
        # Invalid or deleted session
        st.session_state.current_session_id = None
        current_session_id = None

# Render Welcome Banner if fresh session
if not current_session_id or len(messages) == 0:
    st.markdown("""
    <div style="background:#f0f4ff; border-radius:12px; padding:1.2rem; border-left:4px solid #4361ee; margin-bottom:1.5rem;">
        <h3 style="margin-top:0; color:#3a0ca3;">👋 Hello! What doubt can I help you with today?</h3>
        <p style="margin-bottom:0; color:#475569;">
            Type your question below, or snap & upload a photo of your textbook question. 
            I'll explain it step-by-step with formulas, concepts, and practice problems!
        </p>
    </div>
    """, unsafe_allow_html=True)


# Render Existing Messages in Active Chat
for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_path") and os.path.exists(msg["image_path"]):
            st.image(msg["image_path"], caption="Uploaded question photo", width=360)
        
        st.markdown(msg["content"], unsafe_allow_html=True)

        # Feedback Buttons on Assistant Responses
        if msg["role"] == "assistant":
            col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 10])
            user_rating = db.get_feedback_for_message(msg["id"], user["id"])
            
            with col_fb1:
                up_label = "👍 Liked" if user_rating == 1 else "👍"
                if st.button(up_label, key=f"fb_up_{msg['id']}"):
                    db.save_feedback(msg["id"], user["id"], rating=1)
                    st.toast("Thank you for the positive feedback! 🌟")
                    st.rerun()

            with col_fb2:
                down_label = "👎 Disliked" if user_rating == -1 else "👎"
                if st.button(down_label, key=f"fb_down_{msg['id']}"):
                    db.save_feedback(msg["id"], user["id"], rating=-1)
                    st.toast("Feedback noted. We will improve this explanation.")
                    st.rerun()


# ---------------- DOUBT INPUT SECTION ---------------- #
st.markdown("---")
st.markdown("#### 💬 Ask Your Doubt / Follow-up")

with st.expander("📷 Upload Question Image or 🎙️ Voice Input (Optional)", expanded=False):
    uploaded_image = st.file_uploader(
        "Upload photo of textbook, worksheet, or handwritten question",
        type=["png", "jpg", "jpeg", "webp"],
        key="doubt_image_uploader",
        help="Max file size: 5 MB"
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Image Preview", width=260)

    # Audio input if supported
    audio_val = None
    if hasattr(st, "audio_input"):
        audio_val = st.audio_input("Record your question with voice (Optional)")

# Text input for the doubt
user_doubt = st.chat_input("Type your question or follow-up here (e.g. 'Solve 3x + 5 = 20' or 'Explain step 2 again')...")

if user_doubt:
    # Validate image if provided
    img_valid, saved_img_path, pil_img, img_err = utils.validate_and_save_image(uploaded_image)
    if not img_valid:
        st.error(img_err)
    else:
        # Check if creating a new session or continuing
        is_followup = bool(current_session_id and len(messages) > 0)
        
        if not current_session_id:
            current_session_id = str(uuid.uuid4())
            session_title = user_doubt.strip()[:50] or "Photo Doubt"
            db.create_chat_session(
                session_id=current_session_id,
                user_id=user["id"],
                title=session_title,
                class_level=selected_class,
                board=selected_board,
                subject=selected_subject,
                language=selected_language,
                mode=selected_mode
            )
            st.session_state.current_session_id = current_session_id

        # 1. Save user message to database
        db.add_message(
            session_id=current_session_id,
            role="user",
            content=user_doubt,
            image_path=saved_img_path
        )

        # 2. Display user message immediately
        with st.chat_message("user"):
            if saved_img_path and os.path.exists(saved_img_path):
                st.image(saved_img_path, caption="Uploaded question photo", width=360)
            st.markdown(user_doubt)

        # 3. Generate Solution with AI
        with st.chat_message("assistant"):
            with st.spinner("🧑‍🏫 AI Teacher is preparing your step-by-step solution..."):
                # Fetch recent conversation history for multi-turn context
                existing_msgs = db.get_session_messages(current_session_id)
                success, ai_response = llm.generate_doubt_solution(
                    doubt_text=user_doubt,
                    class_level=selected_class,
                    board=selected_board,
                    subject=selected_subject,
                    language=selected_language,
                    mode=selected_mode,
                    image=pil_img,
                    chat_history=existing_msgs[:-1], # pass history before the latest user message
                    is_followup=is_followup
                )

                # Save assistant response to DB
                ai_msg_id = db.add_message(
                    session_id=current_session_id,
                    role="assistant",
                    content=ai_response
                )

                st.markdown(ai_response, unsafe_allow_html=True)
                st.rerun()
