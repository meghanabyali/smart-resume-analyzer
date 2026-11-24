"""Module 4 - feedback reflects detected issues and is well-formed."""
from conftest import STRONG_RESUME, WEAK_RESUME, make_docx, upload_and_analyze

REQUIRED_FIELDS = {"category", "priority", "title", "issue", "evidence", "recommendation", "explanation"}


def titles(analysis):
    return {f["title"] for f in analysis["feedback"]}


def test_feedback_items_well_formed_and_sorted(client, weak_docx):
    a = upload_and_analyze(client, weak_docx, "weak.docx", "web_developer")
    order = {"High": 0, "Medium": 1, "Low": 2}
    prios = [order[f["priority"]] for f in a["feedback"]]
    assert prios == sorted(prios)
    for f in a["feedback"]:
        assert REQUIRED_FIELDS <= set(f)
        assert all(f[k] for k in REQUIRED_FIELDS)
    assert len(titles(a)) == len(a["feedback"])  # no duplicates


def test_weak_resume_gets_spec_example_suggestions(client, weak_docx):
    t = titles(upload_and_analyze(client, weak_docx, "weak.docx", "web_developer"))
    for expected in ["Improve resume formatting", "Add technical projects", "Include certifications",
                     "Add internship experience", "Add SQL skill"]:
        assert expected in t, expected


def test_strong_resume_does_not_get_irrelevant_suggestions(client, strong_docx):
    t = titles(upload_and_analyze(client, strong_docx, "strong.docx", "data_analyst"))
    for absent in ["Add technical projects", "Include certifications", "Add internship experience",
                   "Add SQL skill", "Add your email address", "Improve resume formatting"]:
        assert absent not in t, absent


def test_missing_sql_triggers_sql_suggestion(client):
    text = STRONG_RESUME.replace("SQL queries with joins and aggregations", "queries").replace("SQL, ", "") \
        .replace("in SQL, Python", "in Python")
    a = upload_and_analyze(client, make_docx(text), "nosql.docx", "data_analyst")
    assert "SQL" in a["details"]["skills"]["missing"]
    sql = next(f for f in a["feedback"] if f["title"] == "Add SQL skill")
    assert sql["priority"] == "High"  # SQL is a core Data Analyst keyword
    assert sql["recommendation"].startswith("If you")  # conditional phrasing, never "claim it"


def test_cloud_role_suggests_cloud_technologies(client, weak_docx):
    assert "Mention cloud technologies" in titles(upload_and_analyze(client, weak_docx, "w.docx", "cloud_engineer"))


def test_react_project_suggestion(client):
    text = WEAK_RESUME + "\nSKILLS\nHTML, CSS, JavaScript, React\nPROJECTS\nCollege fest website built with HTML and CSS"
    t = titles(upload_and_analyze(client, make_docx(text), "r.docx", "web_developer"))
    assert "Include React projects" in t


def test_feedback_persisted_in_database(app, client, weak_docx):
    from app.models import Analysis
    a = upload_and_analyze(client, weak_docx, "w.docx", "ai_engineer")
    with app.app_context():
        stored = Analysis.query.filter_by(public_id=a["id"]).one()
        assert len(stored.feedback_items) == len(a["feedback"]) > 0
