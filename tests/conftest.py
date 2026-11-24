"""Shared pytest fixtures: isolated app/database and synthetic documents built in memory."""
import io
import os
import sys

import fitz
import pytest
from docx import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.config import TestingConfig  # noqa: E402
from app.models import db  # noqa: E402

STRONG_RESUME = """Priya Nair
priya.nair@example.com | +91 98765 12345 | linkedin.com/in/priya-sample | github.com/priya-sample

PROFESSIONAL SUMMARY
Aspiring Data Analyst and final-year Computer Science student skilled in SQL, Python and Power BI,
passionate about turning data into business insights.

EDUCATION
B.Tech in Computer Science, Sample Institute of Technology, 2021 - 2025, CGPA 8.6/10

TECHNICAL SKILLS
Python, SQL, Excel, Power BI, Tableau, Pandas, NumPy, Statistics, Data Cleaning, Data Visualization, Git

PROJECTS
Sales Dashboard
- Built a Power BI dashboard on 40,000 sales records and reduced reporting time by 35%.
- Wrote SQL queries with joins and aggregations to model monthly revenue.
Churn Analysis
- Performed data analysis with Python and Pandas on 7,000 customer records.
- Developed a data cleaning pipeline and presented insights to 3 teams.

INTERNSHIP EXPERIENCE
Data Analyst Intern, Example Analytics | Jun 2024 - Aug 2024
- Automated Excel reports with Python, saving 5 hours per week.
- Analyzed campaign data and visualized results in Tableau.

CERTIFICATIONS
Google Data Analytics Professional Certificate (2024)
"""

WEAK_RESUME = """Rahul Verma
I am a student. I know HTML and CSS and some JavaScript. I made a website for my college fest and I like
learning new things. I studied at Sample College. I want a job in a good company where I can grow."""


def make_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        if line.strip().isupper() and line.strip():
            doc.add_heading(line.strip().title(), level=1)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    lines = text.split("\n")
    for start in range(0, len(lines), 55):
        page = doc.new_page()
        y = 50
        for line in lines[start:start + 55]:
            page.insert_text((50, y), line.replace("•", "-"), fontsize=9)
            y += 13
    data = doc.tobytes()
    doc.close()
    return data


def make_image_only_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 60), False)
    pix.clear_with(200)
    page.insert_image(fitz.Rect(50, 50, 300, 300), pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture()
def app(tmp_path):
    class Cfg(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        MAX_UPLOAD_MB = 1
        MAX_CONTENT_LENGTH = 1024 * 1024 + 64 * 1024

    application = create_app(Cfg)
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def strong_docx():
    return make_docx(STRONG_RESUME)


@pytest.fixture()
def strong_pdf():
    return make_pdf(STRONG_RESUME)


@pytest.fixture()
def weak_docx():
    return make_docx(WEAK_RESUME)


def upload(client, content: bytes, name: str):
    return client.post("/api/resumes/upload", data={"resume": (io.BytesIO(content), name)},
                       content_type="multipart/form-data")


def upload_and_analyze(client, content: bytes, name: str, role: str = "data_analyst"):
    r = upload(client, content, name)
    assert r.status_code == 201, r.get_json()
    rid = r.get_json()["resume"]["id"]
    r2 = client.post("/api/analyze", json={"resume_id": rid, "role": role})
    assert r2.status_code == 201, r2.get_json()
    token = r2.get_json()["analysis_id"]
    return client.get(f"/api/analysis/{token}").get_json()["analysis"]
