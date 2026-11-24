# Testing

## Running the automated tests

```bash
# from the project root, with the virtual environment active
python -m pytest            # whole suite
python -m pytest -v         # verbose, one line per test
python -m pytest tests/test_ats.py -k alias   # a subset
```

Each test gets an isolated temporary SQLite database and upload folder (`tests/conftest.py`). Test documents (PDF/DOCX, an image-only "scanned" PDF, corrupted and oversized files) are generated in memory, so no personal data is involved.

## Latest recorded run

Executed on 17 Nov 2026, Windows 11, Python 3.11.9, spaCy 3.7.5 + `en_core_web_sm` 3.7.1:

```
62 passed in 12.44s
```

| File | Tests | Covers |
|---|---:|---|
| `test_parser.py` | 17 | Upload validation (extension, content signature, empty, oversize), PDF/DOCX extraction, corrupted and scanned PDFs, empty DOCX, text cleaning, technical tokenisation, heading detection, contact regexes (incl. "year range is not a phone"), full information extraction, no invented fields, NLP keywords |
| `test_scoring.py` | 14 | Scores within 0–100 for all 4 roles × 2 resumes, parameters ≤ max, total = sum of parameters, six parameters present and explained, determinism, strong > weak, contact score reacts to removed email/phone, categories |
| `test_ats.py` | 9 | All roles configured and consistent with the dictionary, aliases, no substring false positives (Java/JavaScript, SQL/MySQL, Git/GitHub), C++/C#/Node.js/CI-CD, context rule for "ML", multi-word phrases, skill-gap partition, role change changes ATS results, ATS = weighted sum |
| `test_feedback.py` | 7 | Feedback fields complete, sorted by priority, no duplicates; spec example suggestions appear for a weak resume and do not appear for a strong one; missing SQL → High "Add SQL skill" phrased conditionally; cloud and React rules; feedback persisted |
| `test_routes.py` | 15 | Health, pages, security headers, roles API, PDF+DOCX upload storing data and files, validation errors (400/413/415/422), path-traversal filename, scanned-PDF message, analyze validation, 404s, unguessable tokens, **end-to-end Upload → Extract → Analyze → Store → Dashboard → Report (PDF contents verified)**, delete, retention purge |

## Results on the sample dataset

Produced by `python scripts/seed_data.py --samples` on the same date:

| Sample | Role | Resume score | Category | Est. ATS |
|---|---|---:|---|---:|
| data_analyst_strong.pdf | Data Analyst | 99 | Excellent | 100 |
| ai_engineer_strong.pdf | AI Engineer | 96 | Excellent | 100 |
| web_developer_strong.docx | Web Developer | 95 | Excellent | 100 |
| cloud_engineer_average.pdf | Cloud Engineer | 82 | Good | 67 |
| data_analyst_average.docx | Data Analyst | 66 | Needs Improvement | 50 |
| web_developer_incomplete.pdf | Web Developer | 52 | Needs Improvement | 45 |
| cloud_engineer_incomplete.docx | Cloud Engineer | 38 | Significant Improvement Needed | 30 |
| ai_engineer_poorly_structured.docx | AI Engineer | 25 | Significant Improvement Needed | 52 |

The scores rank the samples in the intended quality order. The poorly structured resume has a relatively high ATS score because it mentions many AI keywords – but its resume score is the lowest because it has no sections, contact phone, projects or education structure, which is exactly the distinction between the two scores.

## Manual / UI test checklist

Performed against the running development server (`python run.py`) on 17 Nov 2026. Screenshots were captured with headless Microsoft Edge at 1300 px, 768 px and 576 px widths.

| Check | Result |
|---|---|
| Home, Upload, About, Dashboard, Report pages return 200 | Pass |
| Upload sample PDF & DOCX via `curl` → analyze → dashboard → PDF download | Pass |
| Dashboard charts render with real data (parameter bar chart, ATS chart, rings, meters) | Pass (after fixing a clipped axis label) |
| Recommendation priority filter | Implemented; verify by clicking |
| Desktop layout (1300 px) | Pass |
| Tablet / small layout (768 px, 576 px) – cards stack, navbar collapses, no horizontal overflow | Pass |
| Phone width (390 px) | Not verifiable with headless Edge (it enforces a ~500 px minimum window); check on a real phone or DevTools device mode |
| Drag-and-drop upload, loading indicator, error alerts | Implemented; verify manually in a browser (not automated) |
| Printable report (Ctrl+P) | Implemented with print CSS; verify manually |
| Delete button removes the analysis and redirects | API covered by automated test; click-through verify manually |

### Manual test script

1. `python run.py`, open http://127.0.0.1:5000.
2. Upload `data/sample_resumes/data_analyst_average.docx`, role *Data Analyst* → expect score ≈ 66, ATS ≈ 50, "Add SQL skill" (High).
3. Re-analyse the same file as *Cloud Engineer* → ATS drops, "Mention cloud technologies" appears.
4. Upload a `.txt` file → "Unsupported file type" error. Upload a > 5 MB PDF → "too large" error.
5. On the dashboard: toggle *Table view*, filter recommendations by High/Medium/Low, click *Download Report*.
6. Click the trash icon → confirm → redirected with "permanently deleted"; reopening the old dashboard URL returns 404.
