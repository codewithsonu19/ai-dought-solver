"""
UI and helper utilities for AI Doubt Solver.
Includes dynamic subject mapping by grade, board choices, image validation & storage,
and student-friendly CSS styling.
"""

import os
import uuid
from typing import List, Tuple, Optional
from PIL import Image
import streamlit as st

MAX_IMAGE_SIZE_MB = 5.0
MAX_IMAGE_BYTES = int(MAX_IMAGE_SIZE_MB * 1024 * 1024)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

BOARD_OPTIONS = [
    "CBSE",
    "ICSE",
    "State Board",
    "Other"
]

LANGUAGE_OPTIONS = [
    "English",
    "Hindi",
    "Hinglish"
]

EXPLANATION_MODES = [
    "Step-by-Step",
    "Quick Answer",
    "Explain Like I'm Younger"
]


def get_subjects_for_class(class_level: int) -> List[str]:
    """
    Return dynamic subjects appropriate for the selected grade:
    - Classes 1–5: English, Hindi, Maths, EVS
    - Classes 6–10: Maths, Science, Social Science, English, Hindi
    - Classes 11–12: Physics, Chemistry, Maths, Biology, Accountancy, Business Studies, Economics, Computer Science, English
    """
    if class_level <= 5:
        return ["Maths", "English", "Hindi", "EVS"]
    elif class_level <= 10:
        return ["Maths", "Science", "Social Science", "English", "Hindi"]
    else:
        return [
            "Physics",
            "Chemistry",
            "Maths",
            "Biology",
            "Accountancy",
            "Business Studies",
            "Economics",
            "Computer Science",
            "English"
        ]


def validate_and_save_image(uploaded_file) -> Tuple[bool, Optional[str], Optional[Image.Image], str]:
    """
    Validate uploaded image file size (< 5MB), verify valid image format,
    and save locally for session records.
    Returns (is_valid, saved_path, pil_image, error_message).
    """
    if uploaded_file is None:
        return True, None, None, ""

    # Check byte size limit
    if uploaded_file.size > MAX_IMAGE_BYTES:
        return False, None, None, f"Image file is too large ({uploaded_file.size / (1024*1024):.1f} MB). Maximum allowed size is {MAX_IMAGE_SIZE_MB} MB."

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        image = Image.open(uploaded_file)
        # Convert RGBA/P to RGB for safe saving
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Resize if overly massive (> 2048px on max dimension)
        max_dim = 2048
        if max(image.size) > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        unique_filename = f"{uuid.uuid4().hex[:12]}_{uploaded_file.name.replace(' ', '_')}"
        save_path = os.path.join(UPLOAD_DIR, unique_filename)
        image.save(save_path, quality=90, optimize=True)

        return True, save_path, image, ""
    except Exception as e:
        return False, None, None, f"Could not process image file: {str(e)}"


def load_image_from_path(image_path: str) -> Optional[Image.Image]:
    """Load an image from disk if it exists."""
    if image_path and os.path.exists(image_path):
        try:
            return Image.open(image_path)
        except Exception:
            return None
    return None


def apply_custom_styles() -> None:
    """Inject student-friendly responsive custom CSS."""
    st.markdown("""
    <style>
    /* Google Fonts & Modern Base */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Primary Branding Gradient */
    .brand-header {
        background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
        padding: 1.5rem;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(67, 97, 238, 0.25);
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-tagline {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.3rem;
        font-weight: 400;
    }

    /* Auth Card Layout */
    .auth-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 8px 30px rgba(0,0,0,0.06);
        max-width: 480px;
        margin: 0 auto 2rem auto;
    }

    /* Student Badge */
    .student-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        background: #e0e7ff;
        color: #3730a3;
        margin-right: 6px;
    }

    /* Solution Box Styling */
    .solution-card {
        background-color: #f8fafc;
        border-left: 5px solid #4361ee;
        border-radius: 8px;
        padding: 1rem 1.4rem;
        margin: 1rem 0;
    }

    /* Practice expander */
    details {
        background: #f1f5f9;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        cursor: pointer;
    }
    details summary {
        font-weight: 600;
        color: #3b82f6;
    }

    /* Flash Notice banner */
    .flash-notice {
        padding: 12px 18px;
        border-radius: 10px;
        font-weight: 500;
        margin-bottom: 1.2rem;
    }
    .flash-success { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
    .flash-error   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .flash-warning { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .flash-info    { background: #e0f2fe; color: #075985; border: 1px solid #bae6fd; }

    /* Buttons styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    </style>
    """, unsafe_allow_html=True)


def render_flash_messages() -> None:
    """Render and clear any flash notice in session state."""
    msg = st.session_state.get("flash_message")
    msg_type = st.session_state.get("flash_type", "info")
    if msg:
        if msg_type == "success":
            st.success(msg)
        elif msg_type == "error":
            st.error(msg)
        elif msg_type == "warning":
            st.warning(msg)
        else:
            st.info(msg)
        st.session_state.flash_message = None
        st.session_state.flash_type = "info"


def render_brand_header(title: str = "AI Doubt Solver", subtitle: str = "Instant, Step-by-Step Help for Classes 1 to 12 (CBSE / ICSE / State Boards)") -> None:
    """Render the main student-friendly brand header banner."""
    st.markdown(f"""
    <div class="brand-header">
        <h1 class="brand-title">🎓 {title}</h1>
        <div class="brand-tagline">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)
