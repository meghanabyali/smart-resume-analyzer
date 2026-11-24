# Demo Video Script (≈ 5 minutes)

No video has been recorded yet. This is the script and recording plan.

## Setup before recording

1. `python run.py` and open http://127.0.0.1:5000 in a maximised browser window (zoom 100–110%).
2. Have these files ready in a folder: `data/sample_resumes/data_analyst_average.docx` and `data/sample_resumes/data_analyst_strong.pdf`, plus any `.txt` file for the error demo.
3. Recording tool: OBS Studio or the Windows Game Bar (`Win + Alt + R`), 1080p, microphone on.
4. Close notifications and other tabs.

## Recording sequence

| # | Time | Screen | Narration |
|---|---|---|---|
| 1 | 0:00–0:25 | Title slide of the PPT, then the app's Home page | "This is Smart Resume Analyzer, an AI capstone project that scores resumes, checks ATS compatibility, finds skill gaps and gives explainable feedback, using rule-based AI and NLP with spaCy and NLTK." |
| 2 | 0:25–0:45 | Scroll the Home page: features, "How it works" | "The workflow follows the specification's seven steps, from upload to dashboard." |
| 3 | 0:45–1:10 | Upload page: drag the `.txt` file in | "Validation happens in the browser and again on the server. Unsupported files are rejected, and the server also checks the real file signature, size, and whether the PDF is scanned or password-protected." |
| 4 | 1:10–1:35 | Drag `data_analyst_average.docx`, choose **Data Analyst**, click **Analyze Resume** | "I upload an average student resume and pick Data Analyst. The progress steps show upload, text extraction, then scoring and feedback." |
| 5 | 1:35–2:15 | Dashboard top: summary cards, score ring, ATS ring | "The resume scores 66, Needs Improvement. The estimated ATS score is 50: 60% keyword coverage, 20% parseability and 20% structure. It is clearly labelled as an estimate." |
| 6 | 2:15–2:45 | Parameter chart (hover a bar), click **Table view**; skills card | "Here is each of the six parameters. Only 3 of 13 Data Analyst keywords were found, and SQL, Power BI and Tableau are missing. Missing means not found in the text, not that the student lacks the skill." |
| 7 | 2:45–3:25 | Smart Recommendations: click **High**, read "Add SQL skill"; then **All** | "Every suggestion lists the problem, the evidence from the resume, the recommendation and why it matters. They are sorted by priority, and skill advice is always conditional: 'If you have used SQL…'." |
| 8 | 3:25–3:45 | Score Explanation accordion (open Projects); Extracted Information panel | "The score is fully explainable, showing what was found and what was missing. On the right are the details extracted with regex and spaCy NER, and the top NLP keywords." |
| 9 | 3:45–4:05 | Click **Download Report**, open the PDF | "The PDF report is generated with ReportLab from the stored analysis." |
| 10 | 4:05–4:30 | Analyze Another Resume → `data_analyst_strong.pdf` → dashboard | "For comparison, a strong resume scores 99 with full keyword coverage, and no improvement rules fire." |
| 11 | 4:30–4:45 | Click the trash icon → confirm | "Users can permanently delete their data. Records also expire automatically after the retention period." |
| 12 | 4:45–5:00 | Terminal: `python -m pytest` showing **62 passed**; README | "The project includes 62 automated tests, documentation and a Render deployment configuration. Thank you." |

## Expected output (for checking the recording)

| Input | Expected |
|---|---|
| `.txt` file | Red alert: "Unsupported file type…" |
| `data_analyst_average.docx` + Data Analyst | Resume score 66 (Needs Improvement), ATS 50, 3 matched / 10 missing, High: "Add SQL skill", "Mention BI / visualization tools", "Cover more role-relevant keywords" |
| `data_analyst_strong.pdf` + Data Analyst | Resume score 99 (Excellent), ATS 100, 13/13 matched, no recommendations |
| Same average resume + Cloud Engineer (optional) | Lower ATS; "Mention cloud technologies" appears |

## After recording

Trim pauses, add the title slide as an intro card, export as MP4 (1080p), upload it (for example to YouTube as Unlisted, or to Google Drive), and paste the link into the README and the submission form.
