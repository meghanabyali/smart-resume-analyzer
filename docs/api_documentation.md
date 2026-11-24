# API Documentation

Base URL: `http://localhost:5000` (local). All API responses are JSON with a `success` boolean; errors include a user-safe `error` message. Identifiers (`resume_id`, `analysis_id`) are random access tokens.

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Home page |
| GET | `/upload` | Upload page |
| GET | `/about` | About page |
| GET | `/dashboard/<analysis_id>` | Analysis dashboard (HTML) |
| GET | `/report/<analysis_id>` | Printable report (HTML) |
| GET | `/health` | Health check |
| GET | `/api/roles` | List target roles |
| POST | `/api/resumes/upload` | Upload + extract + store a resume |
| GET | `/api/resumes/<resume_id>` | Stored resume summary |
| DELETE | `/api/resumes/<resume_id>` | Delete resume, analyses, feedback and file |
| POST | `/api/analyze` | Run scoring, ATS analysis, skill gap and feedback |
| GET | `/api/analysis/<analysis_id>` | Full analysis result |
| DELETE | `/api/analysis/<analysis_id>` | Delete the analysis and its resume (all personal data) |
| GET | `/api/reports/<analysis_id>/pdf` | Download PDF report |

## GET /health
```json
{"status": "ok", "database": true, "nlp_backend": "spaCy en_core_web_sm"}
```
Returns 503 if the database is unreachable.

## GET /api/roles
```json
{"success": true, "roles": [{"id": "data_analyst", "title": "Data Analyst", "description": "...", "keywords": ["Python", "SQL", "..."]}]}
```

## POST /api/resumes/upload
`multipart/form-data` with field `resume` (PDF or DOCX, ≤ `MAX_UPLOAD_MB`).

```bash
curl -F "resume=@data/sample_resumes/data_analyst_strong.pdf" http://localhost:5000/api/resumes/upload
```
**201**
```json
{"success": true, "resume": {
  "id": "Xq3...token", "original_filename": "data_analyst_strong.pdf", "file_type": "pdf", "file_size": 3561,
  "uploaded_at": "2026-11-17T15:35:10Z", "page_count": 1, "word_count": 352,
  "candidate": {"name": "Ananya Rao", "email": "ananya.rao@example.com", "phone": "+91 98765 43210", "linkedin": "...", "github": "...", "portfolio": null, "name_method": "spaCy named-entity recognition"},
  "sections_detected": ["summary", "education", "skills", "projects", "internships", "certifications", "achievements"]}}
```
| Status | When |
|---|---|
| 400 | no file field |
| 413 | file larger than the limit |
| 415 | unsupported extension, or content does not match the extension |
| 422 | corrupted, password-protected, scanned/image-only, empty or too little text |
| 500 | unexpected error (no internal details exposed) |

## POST /api/analyze
JSON body: `{"resume_id": "<token>", "role": "data_analyst|web_developer|ai_engineer|cloud_engineer"}`

```bash
curl -H "Content-Type: application/json" -d '{"resume_id":"Xq3...","role":"data_analyst"}' http://localhost:5000/api/analyze
```
**201**
```json
{"success": true, "analysis_id": "H__K...", "resume_score": 99, "ats_score": 100, "dashboard_url": "/dashboard/H__K..."}
```
400 – missing `resume_id`/`role` or invalid role · 404 – resume not found.

A resume can be analysed for several roles; each call creates a new analysis.

## GET /api/analysis/<analysis_id>
**200** – abbreviated:
```json
{"success": true, "analysis": {
  "id": "H__K...", "resume_id": "Xq3...", "target_role": "data_analyst", "target_role_title": "Data Analyst",
  "resume_score": 66, "score_category": "Needs Improvement", "ats_score": 50, "keyword_match_percentage": 23.1,
  "parameter_scores": {"structure": 13.0, "skills": 9.8, "education": 15.0, "projects": 8.0, "contact": 12.0, "completeness": 8.0},
  "details": {
    "resume_score": {"total": 66, "raw_total": 65.8, "category": "Needs Improvement", "parameters": [
      {"key": "structure", "label": "Resume Structure", "score": 13.0, "max_score": 20, "percentage": 65,
       "evidence": ["4 standard section heading(s) detected: ..."], "missing": ["Length (56 words, 1 page(s)) is far from the typical range"],
       "explanation": "..."}]},
    "ats": {"score": 50, "formula": "60% role keyword coverage + 20% parseability + 20% structural compatibility",
            "components": [{"key": "keyword_coverage", "name": "Role keyword coverage", "score": 23, "weight": 0.6, "weighted": 13.8, "checks": []}],
            "disclaimer": "..."},
    "skills": {"matched": ["Python", "Excel", "Statistics"], "missing": ["SQL", "..."], "core_missing": ["SQL", "..."],
               "match_percentage": 23.1, "coverage_details": [], "additional_skills": [], "detected_by_category": {}},
    "candidate": {}, "sections_detected": [], "document": {}, "nlp": {"backend": "...", "top_keywords": [], "noun_phrases": []}
  },
  "feedback": [{"category": "ATS Keywords", "priority": "High", "title": "Add SQL skill", "issue": "...", "evidence": "...",
                "recommendation": "If you have used SQL ...", "explanation": "..."}]}}
```
404 if the token does not exist (or was deleted/expired).

## GET /api/reports/<analysis_id>/pdf
Returns `application/pdf` with `Content-Disposition: attachment; filename="resume_analysis_<file>_<role>.pdf"`.

## DELETE /api/analysis/<analysis_id> and DELETE /api/resumes/<resume_id>
**200** `{"success": true, "message": "..."}` – permanently removes the resume, all its analyses, feedback and the stored file.
