"""API, page and end-to-end integration tests (Upload -> Extract -> Analyze -> Store -> Dashboard -> Report)."""
import io
import os

import fitz

from app.models import Analysis, Resume
from conftest import upload, upload_and_analyze


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.get_json()["database"] is True


def test_pages_render(client):
    for url in ["/", "/upload", "/about"]:
        r = client.get(url)
        assert r.status_code == 200, url
        assert b"Smart Resume Analyzer" in r.data


def test_security_headers(client):
    r = client.get("/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in r.headers


def test_roles_endpoint(client):
    roles = client.get("/api/roles").get_json()["roles"]
    assert [r["title"] for r in roles] == ["Data Analyst", "Web Developer", "AI Engineer", "Cloud Engineer"]


def test_upload_pdf_and_docx_store_information(app, client, strong_pdf, strong_docx):
    for content, name in [(strong_pdf, "cv.pdf"), (strong_docx, "cv.docx")]:
        r = upload(client, content, name)
        assert r.status_code == 201, r.get_json()
        res = r.get_json()["resume"]
        assert res["candidate"]["email"] == "priya.nair@example.com"
        assert "skills" in res["sections_detected"]
        with app.app_context():
            stored = Resume.query.filter_by(public_id=res["id"]).one()
            assert "Priya Nair" in stored.extracted_text
            assert os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], stored.stored_filename))


def test_upload_validation_errors(client):
    assert client.post("/api/resumes/upload", data={}).status_code == 400
    r = upload(client, b"plain text", "resume.txt")
    assert r.status_code == 415 and "PDF and DOCX" in r.get_json()["error"]
    assert upload(client, b"not really a pdf", "resume.pdf").status_code == 415
    corrupt = upload(client, b"%PDF-1.4\n%%garbage", "resume.pdf")
    assert corrupt.status_code == 422


def test_oversized_upload_rejected(client):
    big = b"%PDF-1.4\n" + b"0" * (2 * 1024 * 1024)  # test config limit is 1 MB
    r = upload(client, big, "big.pdf")
    assert r.status_code == 413
    assert "too large" in r.get_json()["error"]


def test_path_traversal_filename_is_sanitised(app, client, strong_docx):
    r = upload(client, strong_docx, "../../etc/passwd.docx")
    assert r.status_code == 201
    name = r.get_json()["resume"]["original_filename"]
    assert "/" not in name and ".." not in name
    with app.app_context():
        stored = Resume.query.filter_by(public_id=r.get_json()["resume"]["id"]).one()
        assert os.path.dirname(stored.stored_filename) == ""


def test_scanned_pdf_gets_clear_message(client):
    from conftest import make_image_only_pdf
    r = upload(client, make_image_only_pdf(), "scan.pdf")
    assert r.status_code == 422
    assert "OCR" in r.get_json()["error"]


def test_analyze_validation(client, strong_docx):
    rid = upload(client, strong_docx, "cv.docx").get_json()["resume"]["id"]
    assert client.post("/api/analyze", json={"role": "data_analyst"}).status_code == 400
    assert client.post("/api/analyze", json={"resume_id": rid}).status_code == 400
    bad_role = client.post("/api/analyze", json={"resume_id": rid, "role": "astronaut"})
    assert bad_role.status_code == 400 and "Invalid job role" in bad_role.get_json()["error"]
    assert client.post("/api/analyze", json={"resume_id": "nope", "role": "data_analyst"}).status_code == 404


def test_missing_analysis_returns_404(client):
    assert client.get("/api/analysis/does-not-exist").status_code == 404
    assert client.get("/api/analysis/does-not-exist").get_json()["success"] is False
    assert client.get("/dashboard/does-not-exist").status_code == 404
    assert client.get("/api/reports/does-not-exist/pdf").status_code == 404


def test_tokens_are_unguessable(client, strong_docx):
    a = upload_and_analyze(client, strong_docx, "cv.docx")
    assert len(a["id"]) >= 20 and not a["id"].isdigit()
    assert client.get("/api/analysis/1").status_code == 404


def test_end_to_end_workflow(app, client, strong_pdf):
    # 1-3 upload/extract/process, 4-6 score/ATS/feedback
    a = upload_and_analyze(client, strong_pdf, "priya.pdf", "data_analyst")
    assert a["resume_score"] > 0 and a["ats_score"] > 0
    assert a["details"]["skills"]["matched"]

    # stored in database
    with app.app_context():
        stored = Analysis.query.filter_by(public_id=a["id"]).one()
        assert stored.resume_score == a["resume_score"]
        assert stored.structure_score + stored.skills_score + stored.education_score + stored.projects_score \
            + stored.contact_score + stored.completeness_score == a["details"]["resume_score"]["raw_total"]

    # 7 dashboard shows the real stored results
    page = client.get(f"/dashboard/{a['id']}")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert f'{a["resume_score"]}<small' in html
    assert "Missing skills" in html and "Smart Recommendations" in html
    for kw in a["details"]["skills"]["missing"]:
        assert kw in html

    # printable report + PDF download
    assert client.get(f"/report/{a['id']}").status_code == 200
    pdf = client.get(f"/api/reports/{a['id']}/pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf"
    assert "attachment" in pdf.headers["Content-Disposition"]
    with fitz.open(stream=pdf.data, filetype="pdf") as doc:
        text = "".join(p.get_text() for p in doc)
    assert "Resume Analysis Report" in text
    assert f"{a['resume_score']}/100" in text
    assert "Data Analyst" in text


def test_delete_removes_resume_analyses_and_file(app, client, strong_docx):
    a = upload_and_analyze(client, strong_docx, "cv.docx")
    with app.app_context():
        stored_file = Analysis.query.filter_by(public_id=a["id"]).one().resume.stored_filename
    path = os.path.join(app.config["UPLOAD_FOLDER"], stored_file)
    assert os.path.isfile(path)

    r = client.delete(f"/api/analysis/{a['id']}")
    assert r.status_code == 200
    assert client.get(f"/api/analysis/{a['id']}").status_code == 404
    assert not os.path.exists(path)
    with app.app_context():
        assert Resume.query.count() == 0


def test_retention_purge(app, client, strong_docx):
    from datetime import datetime, timedelta

    from app.models import db
    from app.services.retention import purge_expired

    upload(client, strong_docx, "old.docx")
    with app.app_context():
        app.config["RETENTION_DAYS"] = 7
        r = Resume.query.one()
        r.uploaded_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        assert purge_expired() == 1
        assert Resume.query.count() == 0
