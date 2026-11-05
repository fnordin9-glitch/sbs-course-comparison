from pathlib import Path
from core import Course, derive_course, detect_courses_from_list, make_prompt


def test_derive():
    x = derive_course(Path("FE1234_Buyer_Behaviour.pdf"))
    assert x.code == "FE1234"
    assert x.title == "Buyer Behaviour"


def test_course_match_codes_and_exact_title():
    courses = [
        Course("FE1234", "Buyer Behaviour", "a.pdf", "/a.pdf"),
        Course("FE5678", "Service Marketing", "b.pdf", "/b.pdf"),
        Course("FE123", "Buyer Behaviour Intro", "c.pdf", "/c.pdf"),
    ]
    matches = detect_courses_from_list("Completed: FE1234\nService Marketing", courses)
    assert "FE1234" in matches
    assert "FE5678" in matches
    assert "FE123" not in matches


def test_prompt_has_only_selected():
    course = Course("FE1234", "Buyer Behaviour", "a.pdf", "/a.pdf")
    prompt = make_prompt("[PDF PAGE 1] EXCHANGE", [(course, "[PDF PAGE 2] SBS")])
    assert "FE1234" in prompt
    assert "[PDF PAGE 2]" in prompt
    assert "formal" not in prompt.lower() or "approval" not in prompt.lower()
