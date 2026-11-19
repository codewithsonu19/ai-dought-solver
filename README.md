# 🎓 AI Doubt Solver

> **Instant, Grade-Adaptive AI Doubt Resolution for School Students (Class 1 to 12 — CBSE / ICSE / State Boards)**

AI Doubt Solver is a full-stack educational web application designed specifically for Indian school students. Built with **Streamlit**, **Python 3.11+**, **Gemini API (`google-generativeai`)**, and a hardened **SQLite** backend with **bcrypt** password hashing, it provides step-by-step explanations, formulas, common mistake callouts, and practice questions tailored to each grade band.

---

## 🌟 Key Features

1. **Grade-Adaptive Explanations (Classes 1–12):**
   - **Classes 1–5 (Primary):** Short sentences, friendly emojis (🌟, 🍎), everyday examples (candies, toys), gentle tone.
   - **Classes 6–8 (Middle):** Intuitive analogies, core definitions, encouraging curiosity.
   - **Classes 9–10 (Secondary):** NCERT & Board-exam-focused, step-marking, formula substitution with units, common pitfalls.
   - **Classes 11–12 (Senior):** Rigorous mathematical notation ($\LaTeX$), derivations, numerical analysis, JEE/NEET/CUET tips.
2. **Mandatory Standardized 6-Part Response Format:**
   - 🔍 **Understanding of the Question:** 1-line recap of the objective.
   - 📝 **Step-by-Step Solution:** Clear, numbered mathematical/conceptual steps.
   - 🎯 **Final Answer:** Highlighted result.
   - 💡 **Key Concept / Formula Used:** Highlighting the underlying theorem or formula.
   - ⚠️ **Common Mistake to Avoid:** Trap or calculation error to watch out for.
   - 🚀 **Practice Questions:** 2 practice questions with solutions hidden inside a collapsible expander.
3. **Multimodal & Voice Input:**
   - Type doubts in text box.
   - Upload textbook / handwritten photos (JPEG, PNG, WEBP, up to 5 MB limit).
   - Audio input support.
4. **Dynamic Subjects by Grade:**
   - **Classes 1–5:** Maths, English, Hindi, EVS
   - **Classes 6–10:** Maths, Science, Social Science, English, Hindi
   - **Classes 11–12:** Physics, Chemistry, Maths, Biology, Accountancy, Business Studies, Economics, Computer Science, English
5. **Languages & Explanation Modes:**
   - Languages: **English**, **Hindi** (Devanagari), **Hinglish** (Roman script)
   - Modes: **Step-by-Step**, **Quick Answer**, **Explain Like I'm Younger**
6. **Robust Multi-Tenant Security & Authentication:**
   - Registration with live password strength meter (8+ chars, upper, lower, number, special).
   - Passwords hashed using salted `bcrypt`.
   - Account lockout protection: 5 consecutive failed attempts lock the account for 15 minutes.
   - Password resets via single-use, 20-minute expiring cryptographically secure tokens (`secrets.token_urlsafe`), hashed with SHA-256 before database storage.
   - Non-enumerating responses on password reset to prevent user email scraping.
   - Rate limiting: max 3 reset requests per hour per email; 3-second cooldown between AI queries.
   - Multi-tenant data isolation: each student's chat history and feedback is strictly private.
   - 60-minute inactivity session timeout.
   - Thumbs up (👍) and Thumbs down (👎) feedback stored in SQLite per response.
   - Admin Analytics Dashboard for metrics and student satisfaction.

---

## 🗂️ Project Structure

```text
AI Doubt Solver/
├── app.py                  # Main entrypoint, routing & st.navigation
├── auth.py                 # Bcrypt hashing, lockout, live strength & session validation
├── db.py                   # SQLite schema, parameterized queries & data isolation
├── email_utils.py          # SMTP dispatcher & dev-mode console fallback
├── llm.py                  # Gemini API integration, multimodal & grade simulation
├── prompts.py              # Pedagogical rules, syllabus alignment & system prompts
├── utils.py                # Subject mapping, image validator, audio helper & CSS
├── pages/
│   ├── login.py            # Login page with lockout notification & demo accounts
│   ├── register.py         # Registration with live password meter
│   ├── forgot_password.py  # Password reset request with rate limiting
│   ├── reset_password.py   # Token verification & password update
│   ├── doubt_solver.py     # Main multi-turn doubt solver chat interface
│   ├── history.py          # Searchable, strictly isolated past doubts
│   ├── profile.py          # Edit profile, change password & delete account
│   └── admin.py            # Admin metrics & feedback analytics dashboard
├── tests/
│   ├── test_auth.py        # Bcrypt, strength & token unit tests
│   ├── test_db.py          # DB isolation, cascades & lockout tests
│   ├── test_prompts.py     # Grade band & prompt formatting tests
│   └── test_flows.py       # End-to-end user verification flows
├── sample_doubts.json      # 10 comprehensive curriculum test doubts
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Local runtime configuration
└── README.md               # Complete setup, deployment & usage guide
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.11 or higher
- Git (optional)

### 2. Install Dependencies
```bash
git clone <repo-url>
cd "AI Doubt Solver"
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your configuration:
```env
# Gemini API Key (Get free key from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# App Base URL
APP_BASE_URL=http://localhost:8501

# Development Mode (true: prints reset tokens to console/UI; false: production mode)
DEV_MODE=true

# SMTP Email Configuration (Optional - for real email delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_NAME="AI Doubt Solver Support"

# Session Timeout (Minutes)
SESSION_TIMEOUT_MINUTES=60
```

### 4. Run the Application

#### Option A: Running directly from Python IDLE (Recommended for School Labs)
1. Right-click on [run_app.py](file:///d:/AI%20Doubt%20Solver/run_app.py) or [app.py](file:///d:/AI%20Doubt%20Solver/app.py) and click **"Edit with IDLE"**.
2. In the IDLE window, press **`F5`** (or go to menu: **Run -> Run Module**).
3. The server starts and opens the app in your browser automatically!

#### Option B: Running from Terminal / Command Prompt
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🛠️ Seeded Demo Accounts (DEV_MODE)

When `DEV_MODE=true`, test accounts are pre-seeded automatically:

| Role | Username | Email | Password | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Student** | `demo_student` | `student@example.com` | `Student@123` | Class 10 (CBSE) |
| **Admin** | `demo_admin` | `admin@example.com` | `Admin@123` | Access to Admin Dashboard |

*(When `DEV_MODE=false`, demo account creation is disabled for production security.)*

---

## 📧 SMTP & Gmail App Password Setup

To deliver real password reset emails via Gmail:
1. Go to your **Google Account** > **Security**.
2. Turn on **2-Step Verification** if not already enabled.
3. Search for **App passwords** (or go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Create a new app password named `AI Doubt Solver`.
5. Copy the 16-character generated password into `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_actual_email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop
   ```
*(If SMTP is not configured, the app seamlessly prints the reset link to the console and presents a clickable token in the UI when DEV_MODE is on).*

---

## 🧪 Running Unit & Flow Tests

Run all 18 unit and flow tests with `pytest`:
```bash
python -m pytest -v tests
```

Tests verify:
- ✅ Password strength calculation and validation rules
- ✅ Bcrypt hashing and constant-time password verification
- ✅ Cryptographic token generation and SHA-256 hash checking
- ✅ Single-use reset tokens and expiration enforcement
- ✅ 5 failed login attempts triggering 15-minute account lockout
- ✅ Duplicate email and username registration rejection
- ✅ Multi-tenant data isolation (User A cannot view/delete User B's history)
- ✅ Grade-adaptive prompt synthesis (Class 2 vs 8 vs 12)
- ✅ Multimodal image-based question understanding

---

## 📚 10 Sample Curriculum Test Doubts

The app includes `sample_doubts.json` featuring 10 doubts across 5 key subjects:

1. **Maths (Class 2, CBSE):**
   - *Question:* "Ravi has 7 red apples. His grandmother gives him 5 green apples. How many apples does Ravi have altogether?"
2. **Maths (Class 10, CBSE):**
   - *Question:* "Find the roots of the quadratic equation $2x^2 - 7x + 3 = 0$ using the quadratic formula, and state the nature of the roots."
3. **Science (Class 8, NCERT):**
   - *Question:* "Why is water not used to extinguish fires involving electrical equipment or oil spills? What is the best extinguishing agent instead?"
4. **Science / Physics (Class 12, CBSE):**
   - *Question:* "State Faraday's laws of electromagnetic induction and Lenz's law. A circular coil of 200 turns and radius 10 cm is placed in a uniform magnetic field of 0.5 T perpendicular to the plane. If the field is reduced to zero in 0.1 s, calculate the induced EMF."
5. **English (Class 3, ICSE):**
   - *Question:* "In the sentence 'The fluffy white bunny hopped quickly into the green garden', identify the naming words (nouns) and describing words (adjectives)."
6. **English (Class 10, CBSE):**
   - *Question:* "Convert the following sentence into passive voice: 'The students have submitted all their science assignments to the principal.' Explain the rule for changing the present perfect tense."
7. **Hindi (Class 4, State Board):**
   - *Question:* "सूरज, रात, दोस्त, और जीत - इन शब्दों के विलोम (उलटे अर्थ वाले) शब्द क्या होंगे? एक सरल वाक्य बनाकर समझाइए।"
8. **Hindi (Class 9, CBSE):**
   - *Question:* "'सूर्योदय' और 'हिमालय' का संधि-विच्छेद कीजिए और बताइए कि इनमें कौन-सी संधि है। साथ ही 'राजपुत्र' में कौन-सा समास है?"
9. **Social Science (Class 7, NCERT):**
   - *Question:* "What causes ocean tides, and why do spring tides and neap tides occur? Explain the role of the Moon and the Sun's gravitational pull."
10. **Social Science (Class 10, CBSE):**
    - *Question:* "Why did Mahatma Gandhi decide to withdraw the Non-Cooperation Movement in February 1922? Explain the significance of the Chauri Chaura incident."

---

## ☁️ Deployment to Streamlit Community Cloud

1. Push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of AI Doubt Solver"
   git remote add origin https://github.com/<your-username>/ai-doubt-solver.git
   git push -u origin main
   ```
2. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **"New App"** and select your repository, branch (`main`), and main file path (`app.py`).
4. Click **"Advanced Settings"** and paste your secrets into the **Secrets** section:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   DEV_MODE = "false"
   APP_BASE_URL = "https://your-app-subdomain.streamlit.app"
   SESSION_TIMEOUT_MINUTES = 60
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = 587
   SMTP_USER = "your_email@gmail.com"
   SMTP_PASSWORD = "your_app_password"
   SMTP_FROM_NAME = "AI Doubt Solver"
   ```
5. Click **"Deploy"**. Your AI Doubt Solver will be live globally in under 2 minutes!

---

## 🔒 Security Best Practices Implemented

- **Salted Bcrypt Hashing:** Passwords are never stored in plaintext and never leaked in session dictionaries.
- **Strict Multi-Tenant Isolation:** Database queries enforce `WHERE user_id = ?` filtering on every single read, write, update, and delete operation.
- **Anti-Enumeration Protection:** Forgot password requests always return a uniform confirmation message regardless of whether the email exists.
- **Cryptographic Reset Tokens:** Tokens generated via `secrets.token_urlsafe(32)`; only SHA-256 digests are stored in the database.
- **Single-Use & Expiry:** Reset tokens expire in 20 minutes and are marked used immediately upon consumption.
- **Account Lockout:** 5 failed attempts locks the account for 15 minutes.
- **Child-Safe AI Guardrails:** System prompts enforce child-friendly vocabulary, refuse harmful topics, and never send student passwords or private emails to external LLMs.
- **Sanitized Parameterized SQL:** 100% of SQLite database calls use `?` parameterization to eliminate SQL injection vulnerabilities.

---

## 📄 License
MIT License. Built with ❤️ for students across India.
"# AI-dought-solver" 
