"""
Unit tests for system prompt generation and grade-adaptive instructions.
"""

import prompts


def test_grade_band_classification():
    assert prompts.get_grade_band(1) == "primary"
    assert prompts.get_grade_band(5) == "primary"
    assert prompts.get_grade_band(6) == "middle"
    assert prompts.get_grade_band(8) == "middle"
    assert prompts.get_grade_band(9) == "secondary"
    assert prompts.get_grade_band(10) == "secondary"
    assert prompts.get_grade_band(11) == "senior"
    assert prompts.get_grade_band(12) == "senior"


def test_primary_prompt_contains_kid_friendly_guidance():
    p = prompts.build_system_prompt(class_level=3, board="CBSE", subject="Maths", language="English", mode="Step-by-Step")
    assert "Primary School Student" in p
    assert "emojis" in p.lower()
    assert "Understanding of the Question" in p
    assert "Step-by-Step Solution" in p
    assert "Practice Questions" in p


def test_senior_secondary_prompt_contains_competitive_pointers():
    p = prompts.build_system_prompt(class_level=12, board="CBSE", subject="Physics", language="English", mode="Step-by-Step")
    assert "Senior Secondary Student" in p
    assert "JEE / NEET / CUET" in p
    assert "LaTeX" in p


def test_hindi_language_instruction():
    p = prompts.build_system_prompt(class_level=10, board="State Board", subject="Science", language="Hindi", mode="Step-by-Step")
    assert "Devanagari" in p
