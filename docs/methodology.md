# AI / NLP Methodology

The system uses **explainable rule-based AI with basic NLP** – deliberately no deep learning or LLMs (see the specification's scope limitations). Every number on the dashboard can be traced to a rule and to evidence from the resume.

## 1. Text extraction and preprocessing (Module 1)

| Technique | Implementation |
|---|---|
| PDF text extraction | PyMuPDF `page.get_text("text", sort=True)` (reading order), text blocks for layout analysis |
| DOCX extraction | python-docx, walking the document body in order (paragraphs **and** tables), plus page headers; heading styles and list paragraphs preserved |
| Unicode normalisation | NFKC, ligature repair (`ﬁ → fi`), smart quotes, non-breaking spaces |
| Bullet normalisation | 15+ bullet glyphs (`● ▪ ➢ ✓ -` …) normalised to `• ` so bullet usage can be measured |
| Tokenisation | NLTK `RegexpTokenizer` with a pattern that preserves technical tokens: `C++`, `C#`, `Node.js`, `CI/CD` |
| Stopword removal | NLTK English stopwords + resume boilerplate words (fallback list if NLTK data is unavailable) |
| Lemmatisation | spaCy `en_core_web_sm` lemmatizer |
| Keyword extraction | NLTK `FreqDist` over lemmas + bigrams (n-grams) → top terms shown on the dashboard |
| Key phrases | spaCy dependency-parse noun chunks |

## 2. Information extraction (Module 1)

* **Section identification** – each short line is normalised and compared with ~110 heading synonyms mapped to canonical sections (summary, education, skills, projects, experience, internships, certifications, achievements, activities, other). Handles `ALL CAPS` headings, trailing colons, DOCX heading styles and inline headings (`Skills: Python, SQL`); sub-labels inside a section (`Languages: …`) are not mistaken for new sections.
* **Contact details** – regular expressions for email, phone (10–13 digits, explicitly excluding year ranges like `2019 – 2023`), LinkedIn, GitHub and portfolio URLs.
* **Candidate name** – spaCy named-entity recognition (`PERSON`) on the header lines, retried in title case for ALL-CAPS names, then a layout heuristic (2–4 alphabetic words, not a job title, not a heading). The method used is shown as evidence.
* **Education** – degree patterns (B.Tech, B.E., BCA, M.Sc, MBA, Bachelor, Diploma, Class XII …), institution keywords, years, grades (CGPA, %, x/10), field of study, coursework.
* **Projects / experience** – entry counting, description length, action verbs (50+ verbs such as *developed, deployed, analyzed*), quantified outcomes (`40%`, `10,000 rows`, `200 requests`), date ranges, internship detection.

Fields that cannot be found are stored as `null` – nothing is invented.

## 3. Skill matching (Module 3)

* Dictionary of ~75 canonical skills with aliases (`skill_keywords.json`).
* Each alias compiles to a regex with **technical-term boundaries**: `(?<![a-z0-9+#]) alias (?![a-z0-9+#]|\.[a-z0-9])`
  * `Java` does not match inside `JavaScript`; `SQL` does not match inside `MySQL`; `Git` does not match `GitHub`.
  * `C++`, `C#`, `Node.js` and `CI/CD` match with their punctuation.
* Multi-word phrases tolerate spaces or hyphens (`data cleaning` = `data-cleaning`).
* **Context-aware aliases**: `ML`, `AI`, `JS` count only if a context word (e.g. *model, python, learning* for ML) appears within 120 characters – so "500 ml of solution" is not Machine Learning.
* Skills are detected in the whole resume, in the Skills section and in the Projects section separately (used by scoring and feedback).
* **Skill gap** = role reference keywords − detected skills; core keywords are flagged.

## 4. Resume score (Module 2) – 100 points

Each parameter is computed by an independent function that returns `score, max_score, evidence[], missing[], explanation`. Sub-check points are scaled to the configured maximum (`Config.RESUME_SCORE_WEIGHTS`).

| Parameter (max) | Sub-checks (raw points) |
|---|---|
| Structure (20) | standard headings 1.5 each up to 6 · identity before first section 2 · no repeated sections 2 · readable text (≥60% alphabetic, few garbled chars) 3 · length 250–1100 words & ≤2 pages 7 (partial 4/2) |
| Skills (20) | dedicated skills section 5 · number of identifiable skills (≥12 → 6) · role relevance `6 × min(1, coverage/60%)` · skills clearly listed inside the section 3 |
| Education (15) | section 5 · degree 4 · institution 3 · year 2 · academic detail (field/grade/coursework – optional, 1) |
| Projects (15) | section 4 · ≥2 entries 3 · description ≥60 words 3 · technologies named (1 per skill, max 3) · action verbs 2 |
| Contact (15) | email 5 · phone 4 · name 3 · LinkedIn 2 (optional) · GitHub/portfolio 1 (optional) |
| Completeness (15) | summary 3 · practical evidence (experience/internship or ≥2 projects) 3 · quantified outcomes 3 · ≥350 words 3 · share of sections with real content 3 |

Optional sections (certifications, internships, achievements) are **not** penalised in the score; they only appear as suggestions.

Categories (application-defined): 85–100 Excellent · 70–84 Good · 50–69 Needs Improvement · 0–49 Significant Improvement Needed.

## 5. Estimated ATS compatibility (Module 3) – 100 points

`ATS = 0.60 × keyword coverage + 0.20 × parseability + 0.20 × structural compatibility`

* **Keyword coverage** = matched / reference keywords × 100.
* **Parseability** – text layer extracted (40) · ≥150 words (20) · no garbled/encoding artefacts (20) · simple layout: no multi-column layout (detected from PyMuPDF block positions), ≤2 tables, ≤3 images (20).
* **Structural compatibility** – standard headings (10 each, max 40) · email + phone in plain text (30) · ≤2 pages (15) · bullet formatting (15).

This is a transparent **estimate**, labelled as such everywhere; it is not produced by any commercial ATS.

## 6. Smart feedback (Module 4)

A rule-based decision system with nine generators (`generate_contact_feedback`, `generate_structure_feedback`, `generate_skills_feedback`, `generate_ats_feedback`, `generate_projects_feedback`, `generate_education_feedback`, `generate_experience_feedback`, `generate_completeness_feedback`, `generate_certification_feedback`). Each rule:

1. fires only when its condition is detected (e.g. *no projects section*, *SQL missing for Data Analyst*, *React listed but absent from projects*);
2. produces **category, priority, title, problem, evidence, recommendation, explanation**;
3. sets priority from impact (missing email/phone or core keyword → High; optional links → Low).

`generate_final_recommendations` de-duplicates by title and sorts High → Medium → Low. Skill recommendations are always conditional ("If you have used SQL, list it…") so the system never encourages claiming skills the candidate does not have.

The spec's example suggestions map to rules: *Add SQL skill*, *Include React projects*, *Mention cloud technologies* (role tips in `job_roles.json`); *Improve resume formatting*, *Add technical projects*, *Include certifications*, *Add internship experience* (feedback engine).

## 7. Limitations

* Rule-based heuristics can misread unusual layouts (e.g. text inside images, very creative templates).
* Scanned PDFs are rejected (no OCR in the prototype).
* Keyword dictionaries are starter lists in English; synonyms not in the dictionary are not recognised.
* Scores measure resume presentation and keyword visibility, not candidate ability.
