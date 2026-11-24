# System Architecture

## Overview

A single Flask application (server-rendered Jinja2 pages + a JSON API) with a layered design:

```
Browser (Bootstrap 5, Chart.js, upload.js / dashboard.js)
        │  HTML pages            │  JSON API (/api/*)
        ▼                        ▼
┌────────────────────── Flask routes (app/routes) ──────────────────────┐
│ main_routes   upload_routes   analysis_routes   report_routes         │  thin controllers
└───────────────────────────────┬───────────────────────────────────────┘
                                ▼
┌──────────────── Services (app/services) - no Flask request code ──────┐
│ file_handler ─► resume_parser ─► text_preprocessor ─► section_extractor│  Module 1
│                                   skill_matcher                        │  Module 3
│ resume_scorer                                                          │  Module 2
│ ats_analyzer                                                           │  Module 3
│ feedback_engine                                                        │  Module 4
│ report_generator                                                       │  Module 5
│ analysis_pipeline (orchestrator) · retention (privacy)                 │
└───────────────────────────────┬───────────────────────────────────────┘
                                ▼
           SQLAlchemy models (app/models.py) ─► SQLite / MySQL
           Reference data: data/job_roles.json, data/skill_keywords.json
```

## Workflow (the 7 steps from the specification)

| Step | Where | What happens |
|---|---|---|
| 1. User uploads resume | `upload.js` → `POST /api/resumes/upload` | Drag-and-drop/browse, client-side checks, XHR upload with progress |
| 2. Text extraction | `file_handler.validate_upload`, `resume_parser.extract_document` | Extension + magic-byte + size validation; PyMuPDF / python-docx extraction; scanned, encrypted, corrupted and empty files rejected with clear messages |
| 3. Data processing | `text_preprocessor`, `section_extractor`, `skill_matcher.detect_skills` | Normalisation, section detection, contact/name/education/project/experience extraction, skill detection; stored in `resumes` |
| 4. Resume score | `resume_scorer.calculate_total_resume_score` | Six parameter functions → score /100 + category |
| 5. ATS matching | `skill_matcher.match_role_skills`, `ats_analyzer.calculate_ats_score` | Role keyword coverage, parseability, structure → estimated ATS /100 |
| 6. Suggestions | `feedback_engine.generate_final_recommendations` | Rule-based, prioritised, de-duplicated feedback; stored in `analyses` + `feedback` |
| 7. Dashboard | `GET /dashboard/<token>`, `dashboard.js`; `GET /api/reports/<token>/pdf` | Charts and lists rendered from the stored record; PDF report via ReportLab |

## Folder structure

```
app/
  __init__.py          application factory, error handlers, security headers
  config.py            environment-driven configuration and scoring weights
  models.py            Resume, Analysis, Feedback
  routes/              main_routes, upload_routes, analysis_routes, report_routes
  services/            business logic (see above) + analysis_pipeline, retention, file_handler
  templates/           base, index, upload, dashboard, report, about, error, _macros
  static/              css/style.css, js/upload.js, js/dashboard.js, js/report.js
data/                  role + skill dictionaries, sample resumes, sample job descriptions
tests/                 pytest suite (parser, scoring, ATS, feedback, routes/integration)
scripts/               generate_samples.py, seed_data.py, build_presentation.py
docs/                  this documentation
deliverables/          PPT, project report, demo video script
```

## Database design

```
resumes (1) ──< analyses (1) ──< feedback
```

**resumes** – `id` (PK), `public_id` (unique random token), `original_filename` (sanitised), `stored_filename` (random UUID name), `file_type`, `file_size`, `extracted_text`, `extracted_data_json` (contact, sections, education, projects, experience, skills, document layout), `uploaded_at`.

**analyses** – `id` (PK), `public_id`, `resume_id` (FK), `target_role`, `resume_score`, `ats_score`, `keyword_match_percentage`, `structure_score`, `skills_score`, `education_score`, `projects_score`, `contact_score`, `completeness_score`, `analysis_details_json` (full evidence, ATS components, skill gap, NLP keywords), `created_at`.

**feedback** – `id` (PK), `analysis_id` (FK), `position`, `category`, `priority`, `title`, `issue`, `evidence`, `recommendation`, `explanation`.

Deleting a resume cascades to its analyses and feedback (`cascade="all, delete-orphan"`), and the stored file is removed from disk.

All queries go through the SQLAlchemy ORM (parameterised). Switching to MySQL/PostgreSQL only requires `DATABASE_URL` (plus the DB driver).

## Access control and privacy (no accounts by design)

* Records are addressed only by `public_id` – 144-bit random tokens from `secrets.token_urlsafe(18)`; integer IDs are never exposed.
* `Referrer-Policy: no-referrer` stops tokens leaking to third-party CDNs through the Referer header.
* Delete button on the dashboard (`DELETE /api/analysis/<token>`) removes the resume, analyses, feedback and file.
* `RETENTION_DAYS` (default 7) purges old records at start-up and before each upload.
* Logs contain record IDs and word counts only – never resume text.

## Design decisions

* **Server-rendered templates + small JS** instead of React: keeps the project intermediate-level and deployable as one service.
* **Services independent of Flask requests**: business logic is unit-testable without HTTP.
* **Configurable rules**: scoring weights and categories live in `config.py`; role keywords, aliases and tips live in JSON.
* **Graceful NLP degradation**: if the spaCy model or NLTK data is missing, the app falls back to a blank tokenizer and a built-in stopword list instead of failing.
