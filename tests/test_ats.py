"""Module 3 - keyword extraction, skill matching and ATS score."""
import pytest

from app.config import Config
from app.services.skill_matcher import detect_skills, load_roles, load_skill_dictionary, match_role_skills

DICT = load_skill_dictionary(Config.SKILL_KEYWORDS_FILE)
ROLES = load_roles(Config.JOB_ROLES_FILE)


def skills(text):
    return set(detect_skills(text, DICT))


def test_all_four_roles_configured():
    assert set(ROLES) == {"data_analyst", "web_developer", "ai_engineer", "cloud_engineer"}
    for role in ROLES.values():
        for kw in role["keywords"]:
            assert kw in DICT["by_name"], f"{kw} missing from skill dictionary"


def test_aliases_map_to_canonical_names():
    found = skills("Experienced with JS, ReactJS, GCP, k8s and sklearn")
    assert {"JavaScript", "React", "Google Cloud", "Kubernetes", "Scikit-learn"} <= found


def test_no_false_positives_on_substrings():
    found = skills("I write JavaScript and use MySQL daily. I excelled in GitHub contributions.")
    assert "Java" not in found
    assert "SQL" not in found
    assert "MySQL" in found
    assert "Git" not in found


def test_technical_punctuation_preserved():
    found = skills("Languages: C++, C#, Node.js; pipelines with CI/CD")
    assert {"C++", "C#", "Node.js", "CI/CD"} <= found


def test_ml_alias_requires_context():
    assert "Machine Learning" in skills("Built ML models in Python for classification")
    assert "Machine Learning" not in skills("Added 500 ml of solution to the beaker")


def test_multiword_phrases_and_hyphen_variants():
    found = skills("Strong in data-cleaning, Power BI dashboards and responsive web design")
    assert {"Data Cleaning", "Power BI", "Data Visualization", "Responsive Design"} <= found


def test_match_role_skills_partition():
    detected = detect_skills("Python, SQL and Excel", DICT)
    m = match_role_skills(detected, ROLES["data_analyst"])
    assert set(m["matched"]) == {"Python", "SQL", "Excel"}
    assert set(m["matched"]) | set(m["missing"]) == set(ROLES["data_analyst"]["keywords"])
    assert m["match_percentage"] == round(100 * 3 / len(ROLES["data_analyst"]["keywords"]), 1)


@pytest.fixture()
def analysed(client, strong_docx):
    from conftest import upload
    rid = upload(client, strong_docx, "r.docx").get_json()["resume"]["id"]
    out = {}
    for role in ROLES:
        token = client.post("/api/analyze", json={"resume_id": rid, "role": role}).get_json()["analysis_id"]
        out[role] = client.get(f"/api/analysis/{token}").get_json()["analysis"]
    return out


def test_role_change_affects_ats_analysis(analysed):
    assert analysed["data_analyst"]["ats_score"] > analysed["cloud_engineer"]["ats_score"]
    assert analysed["data_analyst"]["details"]["skills"]["missing"] != analysed["web_developer"]["details"]["skills"]["missing"]


def test_ats_formula_is_weighted_sum(analysed):
    ats = analysed["ai_engineer"]["details"]["ats"]
    expected = sum(c["score"] * c["weight"] for c in ats["components"])
    assert abs(ats["score"] - expected) <= 0.5
    assert [c["weight"] for c in ats["components"]] == [0.6, 0.2, 0.2]
    assert "not a score from" in ats["disclaimer"]
