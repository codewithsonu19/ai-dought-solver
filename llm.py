"""
LLM integration layer for AI Doubt Solver using the Gemini API (google-generativeai).
Handles text queries, multimodal image queries, follow-up chats, rate limiting cooldowns,
and intelligent fallback educational simulations when an API key is not configured.
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import google.generativeai as genai

import prompts

# Default model
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"

# Last request timestamp for rate limiting
_last_request_time = 0.0


def get_api_key() -> Optional[str]:
    """Retrieve Gemini API key from environment."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key and key != "your_gemini_api_key_here":
        return key
    return None


def configure_gemini() -> bool:
    """Configure google-generativeai with API key if available."""
    api_key = get_api_key()
    if api_key:
        try:
            genai.configure(api_key=api_key)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to configure Gemini: {e}")
            return False
    return False


def enforce_cooldown(cooldown_seconds: float = 3.0) -> None:
    """Enforce a brief cooldown between requests to prevent accidental double-clicks or rate limit spikes."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < cooldown_seconds:
        time.sleep(cooldown_seconds - elapsed)
    _last_request_time = time.time()


def generate_doubt_solution(
    doubt_text: str,
    class_level: int,
    board: str,
    subject: str,
    language: str = "English",
    mode: str = "Step-by-Step",
    image: Optional[Image.Image] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    is_followup: bool = False
) -> Tuple[bool, str]:
    """
    Generate an educational solution for a doubt using Gemini or intelligent simulation.
    Returns (success, response_markdown).
    """
    enforce_cooldown(float(os.getenv("AI_REQUEST_COOLDOWN_SECONDS", "3")))

    system_instruction = prompts.build_system_prompt(
        class_level=class_level,
        board=board,
        subject=subject,
        language=language,
        mode=mode
    )

    user_prompt = prompts.build_user_query_prompt(
        doubt_text=doubt_text,
        has_image=(image is not None),
        is_followup=is_followup
    )

    api_key = get_api_key()

    # If API key is present, attempt real Gemini call
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=DEFAULT_GEMINI_MODEL,
                system_instruction=system_instruction
            )

            # Format history if follow-up
            contents = []
            if chat_history and len(chat_history) > 0:
                # Add previous context (limit to last 6 messages to stay within reasonable token windows)
                recent_history = chat_history[-6:]
                chat_session = model.start_chat(history=[])
                for msg in recent_history:
                    role = "user" if msg["role"] == "user" else "model"
                    chat_session.history.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
                
                # Send follow up
                if image is not None:
                    response = chat_session.send_message([user_prompt, image])
                else:
                    response = chat_session.send_message(user_prompt)
            else:
                # Single-turn generation
                parts = [user_prompt]
                if image is not None:
                    parts.append(image)
                response = model.generate_content(parts)

            if response and response.text:
                return True, response.text
            else:
                return False, "Received empty response from Gemini API. Please try rephrasing your question."

        except Exception as e:
            err_msg = str(e)
            print(f"[ERROR] Gemini API Error: {err_msg}")
            
            # If quota or auth failure, provide clear actionable message
            if "API_KEY_INVALID" in err_msg or "400" in err_msg and "key" in err_msg.lower():
                return False, "⚠️ Invalid Gemini API key. Please verify your GEMINI_API_KEY in the .env file."
            elif "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                return False, "⚠️ Gemini API rate limit or quota exceeded. Please wait a moment and try again."
            else:
                # Fallback to simulation if network or unexpected failure occurs in dev mode
                if os.getenv("DEV_MODE", "true").lower() == "true":
                    return True, simulate_grade_response(doubt_text, class_level, board, subject, language, mode, is_followup)
                return False, f"⚠️ AI Service encountered an issue: {err_msg}"

    # No API key provided: Use high quality grade-adaptive simulation
    simulated_solution = simulate_grade_response(
        doubt_text=doubt_text,
        class_level=class_level,
        board=board,
        subject=subject,
        language=language,
        mode=mode,
        is_followup=is_followup
    )
    notice = (
        "> ℹ️ *Note: Running in Demo/Dev Mode without a GEMINI_API_KEY. "
        "To get real-time live answers from Google's Gemini models, add your free `GEMINI_API_KEY` to the `.env` file.*\n\n"
    )
    return True, notice + simulated_solution


def simulate_grade_response(
    doubt_text: str,
    class_level: int,
    board: str,
    subject: str,
    language: str,
    mode: str,
    is_followup: bool
) -> str:
    """
    Generate an authentic, high-quality grade-adaptive sample response following
    the exact 6-part mandatory format for offline and demo testing.
    """
    q_preview = (doubt_text.strip()[:60] + "...") if len(doubt_text.strip()) > 60 else (doubt_text.strip() or "Question from image")

    if class_level <= 5:
        # Primary Class Example
        return f"""### 1. 🔍 Understanding of the Question
We want to understand: **"{q_preview}"** using friendly, real-life examples! 🌟

### 2. 📝 Step-by-Step Solution
1. **Look at what we have:** Imagine you have 6 yummy chocolates 🍫 and your friend brings 4 more chocolates 🍫!
2. **Combine them together:** We count them all up one by one:
   $$6 + 4 = 10$$
3. **Double check our work:** If we take away 4 from 10, we get back our original 6 chocolates ($$10 - 4 = 6$$). Perfect! 🎉

### 3. 🎯 Final Answer
**The answer is 10 chocolates! ⭐**

### 4. 💡 Key Concept / Formula Used
- **Addition ($+$):** Putting groups together to find the total sum!
- Rule: $\\text{{Total}} = \\text{{Part 1}} + \\text{{Part 2}}$

### 5. ⚠️ Common Mistake to Avoid
- Don't rush when counting! Sometimes students count the same item twice or skip zero. Always recount with your fingers or pencil dots! ✏️

### 6. 🚀 Practice Questions
**Question 1:** If Rohan has 8 crayons and gives 3 crayons to Priya, how many crayons are left with Rohan?
**Question 2:** What is $5 + 5$?

<details>
<summary><b>👀 Click here to reveal Practice Solutions</b></summary>

**Answer 1:**
- Step 1: Start with 8 crayons.
- Step 2: Subtract 3: $$8 - 3 = 5$$
- **Final Answer:** Rohan has **5 crayons** left.

**Answer 2:**
- Step 1: Add five and five: $$5 + 5 = 10$$
- **Final Answer:** **10**
</details>
"""
    elif class_level <= 8:
        # Middle School Example
        return f"""### 1. 🔍 Understanding of the Question
We need to analyze and solve the problem: **"{q_preview}"** based on Class {class_level} {board} concepts.

### 2. 📝 Step-by-Step Solution
1. **Identify the Given Information:** Let the unknown quantity be denoted by the variable $x$.
2. **Formulate the Mathematical Relation:**
   According to the problem statement:
   $$2x + 15 = 45$$
3. **Isolate the Variable Term:**
   Subtract $15$ from both sides of the equation:
   $$2x = 45 - 15$$
   $$2x = 30$$
4. **Solve for $x$:**
   Divide both sides by $2$:
   $$x = \\frac{{30}}{{2}} = 15$$

### 3. 🎯 Final Answer
**The value of $x$ is $15$.**

### 4. 💡 Key Concept / Formula Used
- **Linear Equations in One Variable:** Whatever operation (addition, subtraction, multiplication, or division) is applied to the Left Hand Side (LHS), the exact same operation must be applied to the Right Hand Side (RHS) to maintain equality.

### 5. ⚠️ Common Mistake to Avoid
- Forgetting to change the sign when transposing a number across the equals sign ($=$). Remember: $+15$ moves across to become $-15$!

### 6. 🚀 Practice Questions
**Question 1:** Solve the equation for $y$: $$3y - 7 = 14$$
**Question 2:** A number increased by $12$ equals $28$. Find the number.

<details>
<summary><b>👀 Click here to reveal Practice Solutions</b></summary>

**Answer 1:**
- Step 1: $3y = 14 + 7 = 21$
- Step 2: $y = \\frac{{21}}{{3}} = 7$
- **Final Answer:** $y = 7$

**Answer 2:**
- Step 1: Let the number be $n$. Then $n + 12 = 28$.
- Step 2: $n = 28 - 12 = 16$.
- **Final Answer:** The number is **16**.
</details>
"""
    elif class_level <= 10:
        # Secondary Board Exam Example
        return f"""### 1. 🔍 Understanding of the Question
The problem requires finding the solution to **"{q_preview}"** according to Class {class_level} {board} syllabus expectations.

### 2. 📝 Step-by-Step Solution
1. **Standard Form Representation:**
   Express the quadratic equation in standard format $ax^2 + bx + c = 0$:
   $$x^2 - 5x + 6 = 0$$
   Here, comparing with $ax^2 + bx + c = 0$:
   $$a = 1, \\quad b = -5, \\quad c = 6$$

2. **Calculate Discriminant ($D$):**
   $$D = b^2 - 4ac = (-5)^2 - 4(1)(6) = 25 - 24 = 1$$
   Since $D > 0$, the equation has two distinct real roots.

3. **Applying Quadratic Formula:**
   $$x = \\frac{{-b \\pm \\sqrt{{D}}}}{{2a}} = \\frac{{-(-5) \\pm \\sqrt{{1}}}}{{2(1)}} = \\frac{{5 \\pm 1}}{{2}}$$

4. **Calculating the Roots:**
   $$x_1 = \\frac{{5 + 1}}{{2}} = \\frac{{6}}{{2}} = 3$$
   $$x_2 = \\frac{{5 - 1}}{{2}} = \\frac{{4}}{{2}} = 2$$

### 3. 🎯 Final Answer
**The roots of the equation are $x = 3$ and $x = 2$.**

### 4. 💡 Key Concept / Formula Used
- **Quadratic Formula:** $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$
- Nature of roots determined by Discriminant $D = b^2 - 4ac$:
  - $D > 0$: Two distinct real roots
  - $D = 0$: Two equal real roots
  - $D < 0$: No real roots

### 5. ⚠️ Common Mistake to Avoid
- Sign error during $-b$ substitution: when $b = -5$, $-b = -(-5) = +5$. Many students mistakenly write $-5$. Always use brackets during substitution!

### 6. 🚀 Practice Questions
**Question 1:** Find the discriminant of $2x^2 - 4x + 3 = 0$ and state the nature of its roots.
**Question 2:** Solve for $x$ by factorization: $$x^2 - 7x + 12 = 0$$

<details>
<summary><b>👀 Click here to reveal Practice Solutions</b></summary>

**Answer 1:**
- $D = (-4)^2 - 4(2)(3) = 16 - 24 = -8$.
- Since $D < 0$, the equation has **no real roots**.

**Answer 2:**
- $x^2 - 4x - 3x + 12 = 0 \\implies (x - 4)(x - 3) = 0$
- **Final Answer:** $x = 4$ and $x = 3$.
</details>
"""
    else:
        # Senior Secondary (Class 11-12) Example
        return f"""### 1. 🔍 Understanding of the Question
We are tasked with rigorously solving: **"{q_preview}"** aligned with Class {class_level} {board} standards and competitive exams (JEE/NEET).

### 2. 📝 Step-by-Step Solution
1. **Mathematical Formulation & Governing Principle:**
   Consider the function $f(x) = x^3 - 3x + 2$ or the kinematic equation under constant acceleration.
   Using Newton's Second Law:
   $$\\sum \\vec{{F}} = m \\vec{{a}}$$

2. **Integration / Derivative Step:**
   Differentiating with respect to $t$:
   $$v(t) = \\frac{{ds}}{{dt}} = \\frac{{d}}{{dt}}\\left(2t^2 + 5t + 1\\right) = 4t + 5$$
   
3. **Evaluating at the Given Boundary Condition ($t = 3\\text{{ s}}$):**
   $$v(3) = 4(3) + 5 = 12 + 5 = 17 \\text{{ m/s}}$$

4. **Acceleration Determination:**
   $$a(t) = \\frac{{dv}}{{dt}} = \\frac{{d}}{{dt}}(4t + 5) = 4 \\text{{ m/s}}^2$$

### 3. 🎯 Final Answer
**The instantaneous velocity at $t = 3\\text{{ s}}$ is $17\\text{{ m/s}}$ and acceleration is $4\\text{{ m/s}}^2$.**

### 4. 💡 Key Concept / Formula Used
- **Instantaneous Velocity:** $$v = \\lim_{{\\Delta t \\to 0}} \\frac{{\\Delta s}}{{\\Delta t}} = \\frac{{ds}}{{dt}}$$
- **Instantaneous Acceleration:** $$a = \\frac{{dv}}{{dt}} = \\frac{{d^2s}}{{dt^2}}$$
- *JEE / NEET Tip:* Always verify dimensional consistency before finalizing numerical answers.

### 5. ⚠️ Common Mistake to Avoid
- Confusing average velocity ($\\Delta s / \\Delta t$) with instantaneous velocity ($ds/dt$). Never simply divide total displacement at $t=3$ by $3$ when acceleration is present!

### 6. 🚀 Practice Questions
**Question 1:** The position of a particle is given by $x(t) = t^3 - 6t^2 + 9t$. Find the time when the particle momentarily comes to rest ($v = 0$).
**Question 2:** Evaluate the limit: $$\\lim_{{x \\to 0}} \\frac{{\\sin 3x}}{{x}}$$

<details>
<summary><b>👀 Click here to reveal Practice Solutions</b></summary>

**Answer 1:**
- $v(t) = \\frac{{dx}}{{dt}} = 3t^2 - 12t + 9 = 0$
- $3(t^2 - 4t + 3) = 0 \\implies 3(t - 1)(t - 3) = 0$
- **Final Answer:** At $t = 1\\text{{ s}}$ and $t = 3\\text{{ s}}$.

**Answer 2:**
- Standard limit: $\\lim_{{u \\to 0}} \\frac{{\\sin u}}{{u}} = 1$.
- Here: $\\lim_{{x \\to 0}} 3 \\cdot \\frac{{\\sin 3x}}{{3x}} = 3(1) = 3$.
- **Final Answer:** **3**.
</details>
"""
