# Smart Resume Analyzer with AI-Based Feedback

**Artificial Intelligence Capstone Project – Project Report**

Student name(s): ____________________  ·  Institution: ____________________  ·  Date: November 2026

---

## Abstract

Students often submit resumes that are hard for Applicant Tracking Systems (ATS) and recruiters to read. Typical problems are missing sections, poorly presented skills and too few role-specific keywords. This project delivers a web application that analyses PDF and DOCX resumes and gives explainable, actionable feedback. The system extracts text with PyMuPDF and python-docx. It then identifies resume sections and personal details with rule-based NLP (regular expressions, spaCy named-entity recognition and lemmatisation, NLTK tokenisation and frequency analysis).

Each resume receives a score out of 100 across six parameters and an estimated ATS compatibility score for one of four target roles. The system also lists matched and missing skills and generates prioritised recommendations, each backed by evidence. Results are stored in an SQLite database and presented on an interactive dashboard with a downloadable PDF report.

A suite of 62 automated tests passes. On a synthetic dataset of eight resumes, the scores rank the resumes in the intended quality order, from 99 for a strong resume down to 25 for a poorly structured one. The approach stays within the specification's scope: no deep learning, no LLMs and no paid APIs.

## 1. Introduction

Recruitment platforms use automated screening to handle large application volumes. These systems parse a resume into structured fields and search it for role keywords before a recruiter reads it. A resume that looks fine to its author can still score poorly if its sections are unconventional, its text is locked in images or columns, or it lacks the vocabulary of the target role.

This project builds a practical, explainable prototype of that screening logic for students. The system does more than give a number: every score is broken down into the rules that produced it and the evidence found in the resume.

## 2. Problem Statement

Many students create resumes without understanding ATS requirements, industry-relevant technical skills, formatting standards, keyword optimisation or role-specific expectations. As a result, their resumes may contain missing sections, poorly presented technical skills, weak project descriptions and insufficient job-related keywords. A solution is needed that evaluates these aspects and explains, in understandable terms, why a score was assigned and what can be improved.

## 3. Objectives

1. Upload resumes in PDF or DOCX format.
2. Extract and process resume content.
3. Generate resume scores.
4. Check ATS compatibility.
5. Analyze role-based skills.
6. Provide smart improvement suggestions.
7. Display results on a dashboard.

## 4. Background

* **Applicant Tracking Systems** parse resumes into fields (contact, education, experience, skills) and support keyword search and filtering by recruiters. Parsing quality depends on text extractability, standard section headings and simple layouts.
* **Keyword matching** is the simplest form of resume–job matching. Exact matching is brittle: "JS" and "JavaScript" refer to the same skill, while "Java" inside "JavaScript" is a false match. Alias dictionaries and boundary-aware matching address both problems.
* **Rule-based (symbolic) AI** encodes expert knowledge as explicit rules. It is less flexible than machine learning, but it is transparent, deterministic, needs no training data and is easy to audit. Those properties matter when the output is feedback for a person.
* **NLP building blocks** used here are tokenisation, stopword removal, lemmatisation, named-entity recognition, noun-phrase chunking and frequency distributions. These standard techniques are available in spaCy and NLTK.

## 5. Requirements

**Functional:** upload PDF/DOCX; validate type, content and size; extract text; identify sections and contact details; store resume data; score six parameters; analyse four roles; compute an ATS estimate; list matched and missing skills; generate prioritised suggestions; show a dashboard with charts; download a PDF report; delete data.

**Non-functional:** explainable and deterministic results; responses within a few seconds; responsive UI on desktop, tablet and mobile; basic security (file validation, safe storage, unguessable links, no secrets in code); privacy (retention policy, deletion, no logging of resume text); maintainable modular code with automated tests; deployable on Render.

**Technology:** Python 3.11, Flask, Flask-SQLAlchemy, SQLite, spaCy, NLTK, PyMuPDF, python-docx, ReportLab, Bootstrap 5, Chart.js, pytest, Gunicorn.

## 6. System Architecture

The application is a single Flask service with three layers:

1. **Presentation** – Jinja2 templates with Bootstrap 5 for the Home, Upload, Dashboard, Report and About pages. Chart.js draws the charts, and small JavaScript modules handle drag-and-drop upload, progress, filters and deletion.
2. **Routes** – thin controllers that expose HTML pages and a JSON API (`/api/resumes/upload`, `/api/analyze`, `/api/analysis/<id>`, `/api/reports/<id>/pdf`, `/api/roles`, `/health`).
3. **Services** – business logic that does not depend on HTTP: `file_handler`, `resume_parser`, `text_preprocessor`, `section_extractor`, `skill_matcher`, `resume_scorer`, `ats_analyzer`, `feedback_engine` and `report_generator`. `analysis_pipeline` orchestrates them, and `retention` enforces the privacy policy.

Data is stored in three related tables: `resumes` → `analyses` → `feedback`. Role keywords and skill aliases are configurable JSON files. Detailed diagrams are in `docs/architecture.md`.

## 7. Methodology

### 7.1 Module 1 – Upload and parsing
Uploads are checked for extension, file signature (`%PDF-` or a ZIP archive containing `word/document.xml`) and size. Stored files get random UUID names, which prevents path traversal. PyMuPDF extracts PDF text in reading order and analyses text-block positions to detect multi-column layouts. Encrypted, corrupted, empty and image-only (scanned) PDFs are rejected with specific messages. python-docx walks the document body in order, covering paragraphs, tables, page headers, heading styles and list items.

The text is normalised (Unicode, ligatures, bullets, whitespace) and split into sections by matching lines against about 110 heading synonyms. Contact details are extracted with regular expressions; the phone pattern explicitly excludes year ranges. The candidate name comes from spaCy NER with a layout fallback. Further rules capture degrees, institutions, years, grades, projects, action verbs and quantified outcomes.

### 7.2 Module 2 – Resume score
Six independent functions score structure (20), skills (20), education (15), projects (15), contact (15) and completeness (15). Each returns its score, maximum, evidence, gaps and an explanation. Optional items (GPA, certifications, internships, profile links) are never heavily penalised. Score categories are application-defined: Excellent at 85 and above, Good at 70–84, Needs Improvement at 50–69, and Significant Improvement Needed below 50.

### 7.3 Module 3 – ATS keyword checker
About 75 canonical skills, each with aliases, are matched using technical-term boundaries. These preserve `C++`, `C#`, `Node.js` and `CI/CD` and prevent false matches such as Java in JavaScript or SQL in MySQL. Context rules stop ambiguous aliases like "ML" from matching unrelated text. Detected skills are compared with the selected role's reference keywords to produce matched, missing and core-missing lists. The estimated ATS score is 60% keyword coverage, 20% parseability and 20% structural compatibility.

### 7.4 Module 4 – Smart feedback
Nine rule generators produce recommendations, each with a category, priority, problem, evidence, recommendation and explanation. They cover contact details, formatting, skills, ATS keywords and role-specific tips, projects, education, experience and internships, completeness, and certifications. Results are de-duplicated and sorted by priority. Skill-related advice is phrased conditionally ("If you have used SQL…") so users are never encouraged to claim skills they lack.

### 7.5 Module 5 – Dashboard and report
The dashboard shows summary cards, score rings, ATS component meters, a parameter bar chart with a table view, matched and missing skill badges, filterable recommendations, a per-parameter explanation and the extracted information. A printable HTML report and a ReportLab PDF are generated from the stored analysis record.

Full rule tables are in `docs/methodology.md`.

## 8. Implementation

* `app/__init__.py` – application factory, error handlers that return JSON for the API and HTML for pages, security headers (CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy: no-referrer`).
* `app/models.py` – SQLAlchemy models; public access through random 144-bit tokens.
* `app/services/*` – the modules described above (about 2,000 lines of Python).
* `app/templates/*`, `app/static/*` – six pages, one stylesheet and three scripts.
* `data/` – role dictionaries, skill aliases, eight synthetic sample resumes and four sample job descriptions.
* `scripts/` – sample generation, database seeding and presentation build.
* Deployment – `gunicorn.conf.py`, `render.yaml` and the `/health` endpoint.

Screenshots of the running application are in `deliverables/screenshots/`.

## 9. Testing

The pytest suite has 62 tests: 17 parser tests, 14 scoring tests, 9 ATS tests, 7 feedback tests and 15 route/integration tests. They cover validation failures (unsupported, renamed, empty, corrupted, scanned, oversized and path-traversal files) and scoring invariants: bounds, parameter maximums, total equal to the sum of parameters, and determinism. They also cover keyword-matching edge cases, the conditions under which feedback rules fire, the end-to-end flow (upload → extract → analyse → store → dashboard → PDF, with the PDF text verified), deletion and retention.

**Latest run (17 Nov 2026): 62 passed.**

Manual checks confirmed that every page renders and that the dashboard charts display real data. Responsive layouts were checked at 1300, 768 and 576 px. Phone width (390 px) could not be verified with headless Edge, and some interactions are listed for manual browser checks in `docs/testing.md`.

## 10. Results

| Sample resume | Role | Resume score | Category | Est. ATS |
|---|---|---:|---|---:|
| data_analyst_strong.pdf | Data Analyst | 99 | Excellent | 100 |
| ai_engineer_strong.pdf | AI Engineer | 96 | Excellent | 100 |
| web_developer_strong.docx | Web Developer | 95 | Excellent | 100 |
| cloud_engineer_average.pdf | Cloud Engineer | 82 | Good | 67 |
| data_analyst_average.docx | Data Analyst | 66 | Needs Improvement | 50 |
| web_developer_incomplete.pdf | Web Developer | 52 | Needs Improvement | 45 |
| cloud_engineer_incomplete.docx | Cloud Engineer | 38 | Significant Improvement Needed | 30 |
| ai_engineer_poorly_structured.docx | AI Engineer | 25 | Significant Improvement Needed | 52 |

Observations:
* The scores order the resumes as designed, from strong through average to incomplete and poorly structured.
* The two scores measure different things. The poorly structured resume mentions many AI keywords (ATS 52) but has no sections, projects or phone number, so its resume score is only 25.
* Feedback is specific to each resume. The average Data Analyst resume receives 17 suggestions, including the High-priority "Add SQL skill" and "Mention BI / visualization tools". The strong resumes trigger no rules.
* Changing the target role changes the keyword analysis. For example, the strong Data Analyst sample falls from ATS 100 to 40 when analysed for Cloud Engineer and receives "Mention cloud technologies", "Mention containerization" and "Mention Linux skills".

These results come from a small synthetic dataset designed for the project. They demonstrate correct behaviour of the rules, not predictive accuracy against real hiring outcomes.

## 11. Limitations

* Heuristic parsing can misread highly creative layouts and text placed in images or text boxes.
* There is no OCR, so scanned PDFs are detected and rejected.
* Keyword dictionaries are English starter lists, and synonyms outside them are not recognised.
* The ATS score is a transparent estimate, not a commercial ATS result. Neither score measures a candidate's ability.
* There are no user accounts. Access relies on unguessable private links, and there is no rate limiting.
* SQLite on ephemeral hosting loses data on restart unless a persistent disk or managed database is configured.

## 12. Conclusion and Future Scope

The project meets all seven objectives and implements all five modules as a working, tested and deployable prototype. It shows how explainable rule-based AI and basic NLP can give students useful, honest feedback without the cost or opacity of large models.

Future work could add:
* keyword extraction from a pasted job description;
* OCR for scanned resumes;
* an admin page for editing role dictionaries;
* side-by-side comparison of resume versions;
* optional accounts to keep an analysis history.

## References

1. Flask documentation – https://flask.palletsprojects.com/
2. Flask-SQLAlchemy documentation – https://flask-sqlalchemy.palletsprojects.com/
3. spaCy documentation and `en_core_web_sm` model card – https://spacy.io/
4. Bird, S., Klein, E., & Loper, E. *Natural Language Processing with Python* (NLTK book) – https://www.nltk.org/book/
5. PyMuPDF documentation – https://pymupdf.readthedocs.io/
6. python-docx documentation – https://python-docx.readthedocs.io/
7. ReportLab User Guide – https://docs.reportlab.com/
8. Bootstrap 5 documentation – https://getbootstrap.com/docs/5.3/
9. Chart.js documentation – https://www.chartjs.org/docs/
10. Render documentation: Python web services, Blueprints, persistent disks – https://render.com/docs
11. OWASP File Upload Cheat Sheet – https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
12. SkillOrbit, *Artificial Intelligence Capstone Project: Smart Resume Analyzer with AI-Based Feedback* (project specification).
