"""Module 2 - scoring invariants and behaviour."""
from types import SimpleNamespace

import pytest

from app.services.analysis_pipeline import build_analysis
from app.services.resume_scorer import categorise
from conftest import STRONG_RESUME, WEAK_RESUME
from app.services.section_extractor import extract_resume_information


def _fake_resume(text, word_count=None, page_count=1):
    info = extract_resume_information(text)
    data = {k: v for k, v in info.items() if k != "clean_text"}
    data["document"] = {"page_count": page_count, "word_count": word_count or len(text.split()), "metadata": {},
                        "layout": {"multi_column": False, "table_count": 0, "image_count": 0}, "file_type": "pdf"}
    import json
    return SimpleNamespace(extracted_text=info["clean_text"], extracted_data=data,
                           extracted_data_json=json.dumps(data))


@pytest.fixture()
def analyse(app):
    def run(text, role="data_analyst"):
        with app.app_context():
            return build_analysis(_fake_resume(text), role)
    return run


@pytest.mark.parametrize("text", [STRONG_RESUME, WEAK_RESUME])
@pytest.mark.parametrize("role", ["data_analyst", "web_developer", "ai_engineer", "cloud_engineer"])
def test_scores_within_bounds(analyse, text, role):
    r = analyse(text, role)
    total = r["resume_score"]["total"]
    assert 0 <= total <= 100
    assert 0 <= r["ats"]["score"] <= 100
    for p in r["resume_score"]["parameters"]:
        assert 0 <= p["score"] <= p["max_score"], p
    assert abs(total - sum(p["score"] for p in r["resume_score"]["parameters"])) <= 0.5
    assert r["resume_score"]["max_total"] == 100


def test_six_parameters_present(analyse):
    keys = [p["key"] for p in analyse(STRONG_RESUME)["resume_score"]["parameters"]]
    assert keys == ["structure", "skills", "education", "projects", "contact", "completeness"]


def test_every_parameter_is_explained(analyse):
    for p in analyse(WEAK_RESUME)["resume_score"]["parameters"]:
        assert p["explanation"]
        assert p["evidence"] or p["missing"]


def test_deterministic(analyse):
    a, b = analyse(STRONG_RESUME), analyse(STRONG_RESUME)
    assert a["resume_score"] == b["resume_score"]
    assert a["ats"] == b["ats"]


def test_strong_resume_beats_weak_resume(analyse):
    strong, weak = analyse(STRONG_RESUME), analyse(WEAK_RESUME)
    assert strong["resume_score"]["total"] >= 80
    assert weak["resume_score"]["total"] < 50
    assert strong["ats"]["score"] > weak["ats"]["score"]


def test_missing_contact_lowers_contact_score(analyse):
    no_contact = STRONG_RESUME.replace("priya.nair@example.com | +91 98765 12345 | ", "")
    full = next(p for p in analyse(STRONG_RESUME)["resume_score"]["parameters"] if p["key"] == "contact")
    reduced = next(p for p in analyse(no_contact)["resume_score"]["parameters"] if p["key"] == "contact")
    assert reduced["score"] == full["score"] - 9  # email (5) + phone (4)


def test_categories():
    assert categorise(90) == "Excellent"
    assert categorise(70) == "Good"
    assert categorise(55) == "Needs Improvement"
    assert categorise(10) == "Significant Improvement Needed"
