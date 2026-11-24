# Smart Resume Analyzer with AI-Based Feedback

An AI-powered web application that helps students analyse and improve their resumes against industry hiring standards. Upload a PDF or DOCX resume, choose a target role, and get:

- a **resume score out of 100** across six explained parameters,
- an **estimated ATS compatibility score**,
- **matched and missing skills** for the role (skill-gap analysis),
- **prioritised, evidence-backed improvement suggestions**,
- an interactive **dashboard** and a downloadable **PDF report**.

Built with Flask, spaCy, NLTK, PyMuPDF, python-docx, SQLite/SQLAlchemy, Bootstrap 5, Chart.js and ReportLab. The analysis is explainable rule-based AI with basic NLP: no deep learning, no LLMs and no paid APIs, as the project specification requires.

> AI Capstone Project – SkillOrbit specification "Smart Resume Analyzer with AI-Based Feedback".

## Features by module

| Module | What it does |
|---|---|
| 1. Upload & Parsing | Drag-and-drop upload; type/content/size validation; PDF (PyMuPDF) and DOCX (python-docx) extraction; section detection; regex + spaCy NER extraction of name, email, phone, LinkedIn, GitHub, education, projects, experience, certifications; stored in the database |
| 2. Resume Score | Structure 20 · Skills 20 · Education 15 · Projects 15 · Contact 15 · Completeness 15 – each with evidence, gaps and explanation; category label |
| 3. ATS Keyword Checker | Data Analyst, Web Developer, AI Engineer, Cloud Engineer; alias and context-aware keyword matching; ATS = 60% coverage + 20% parseability + 20% structure |
| 4. Smart Feedback | Rule-based recommendations with category, priority, problem, evidence, recommendation, explanation; de-duplicated and sorted |
| 5. Dashboard & Report | Summary cards, score rings, Chart.js parameter chart, skill badges, filterable recommendations, printable report, ReportLab PDF |

## Quick start (local)

Requirements: Python 3.11+, Git.

```bash
git clone <your-repository-url> smart-resume-analyzer
cd smart-resume-analyzer

python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (Git Bash):    source .venv/Scripts/activate
# macOS/Linux:           source .venv/bin/activate

pip install -r requirements.txt                       # includes the spaCy en_core_web_sm model
python -m nltk.downloader -d data/nltk_data stopwords  # optional: app falls back to a built-in list
cp .env.example .env                                   # then set SECRET_KEY

python scripts/generate_samples.py   # (re)create the synthetic sample resumes
python run.py                        # http://127.0.0.1:5000
```

Optional demo data: `python scripts/seed_data.py --samples` analyses every sample resume and prints dashboard links.

### Run the tests

```bash
python -m pytest -v
```
Latest recorded run: **62 passed** (see [docs/testing.md](docs/testing.md)).

## Project structure

```
app/            Flask app: config, models, routes/, services/, templates/, static/
data/           job_roles.json, skill_keywords.json, sample_resumes/, sample_job_descriptions/
tests/          pytest suite (parser, scoring, ATS, feedback, routes + end-to-end)
docs/           architecture, methodology, API, testing, deployment, requirement checklist
scripts/        generate_samples.py, seed_data.py, build_presentation.py
deliverables/   presentation (.pptx), project report, demo video script
run.py · gunicorn.conf.py · render.yaml · requirements.txt · .env.example
```

## Documentation

- [System architecture & database design](docs/architecture.md)
- [AI/NLP methodology & scoring rules](docs/methodology.md)
- [API documentation](docs/api_documentation.md)
- [Testing](docs/testing.md)
- [Deployment (Render)](docs/deployment.md)
- [Requirement checklist / audit](docs/requirements_checklist.md)
- Deliverables: [project report](deliverables/project_report.md) · [presentation](deliverables/Smart_Resume_Analyzer_Presentation.pptx) · [demo video script](deliverables/demo_video_script.md)

## Publishing to GitHub

The repository is initialised locally. To publish it:

```bash
# create an empty repository on github.com first (no README), then:
git remote add origin https://github.com/<your-username>/smart-resume-analyzer.git
git branch -M main
git push -u origin main
```

**GitHub repository:** _add link after publishing_
**Live deployment:** _add link after deploying to Render (see [docs/deployment.md](docs/deployment.md))_

## Privacy & security

- Only PDF/DOCX accepted; extension **and** file signature checked; size limit (default 5 MB).
- Files are stored under random names (no path traversal); original names are sanitised.
- Results are reachable only through unguessable tokens; `Referrer-Policy: no-referrer`; CSP and other security headers.
- One-click deletion from the dashboard; automatic purge after `RETENTION_DAYS` (default 7).
- Resume text is never logged; uploads, database and `.env` are git-ignored.
- Sample resumes are entirely synthetic.

This is a capstone prototype, not a production-hardened system: there are no user accounts or rate limiting, and anyone with a dashboard link can view it.

## Scope & limitations

Deliberately excluded (per the specification): deep learning models, LLM training, complex recommendation engines, enterprise authentication, large-scale cloud architecture. Scanned/image-only PDFs are detected and rejected (no OCR). Scores are transparent estimates. They are not produced by any commercial ATS and do not measure a candidate's ability.
