# Dataset

The specification suggests three data sources. This folder covers them as follows.

| Source (from spec) | What is included | Provenance |
|---|---|---|
| Self-created sample resumes | `sample_resumes/` – 8 synthetic resumes (PDF + DOCX) | Written for this project by `scripts/generate_samples.py`. All names, emails (`example.com`), phone numbers, institutions and companies are fictional. |
| Sample job descriptions | `sample_job_descriptions/` – one per supported role | Self-written illustrative postings, **not** copied from real job ads. |
| Public resume datasets from Kaggle | *Not bundled* (optional) | See below. The application does not depend on Kaggle. |

## Reference dictionaries

* `job_roles.json` – the four roles, their reference keywords, core keywords, role-specific tips and example certifications. Editable starter lists, not definitive hiring requirements.
* `skill_keywords.json` – ~75 canonical technical skills with aliases (e.g. `js → JavaScript`, `gcp → Google Cloud`) and context rules for ambiguous short aliases (`ml`, `ai`, `js`).

## Sample resume matrix

| File | Role | Quality |
|---|---|---|
| `data_analyst_strong.pdf` | Data Analyst | strong |
| `data_analyst_average.docx` | Data Analyst | average |
| `web_developer_strong.docx` | Web Developer | strong |
| `web_developer_incomplete.pdf` | Web Developer | incomplete |
| `ai_engineer_strong.pdf` | AI Engineer | strong |
| `ai_engineer_poorly_structured.docx` | AI Engineer | poorly structured (no headings) |
| `cloud_engineer_average.pdf` | Cloud Engineer | average |
| `cloud_engineer_incomplete.docx` | Cloud Engineer | incomplete |

Regenerate with `python scripts/generate_samples.py`.

## Optional: Kaggle resume dataset

To experiment with real-world resume text (e.g. for testing the extractor on more varied wording):

1. Create a free Kaggle account and search for a public resume dataset (for example, datasets titled "Resume Dataset" that contain resume text by job category). Check the dataset's licence before use.
2. Download it manually or with the Kaggle CLI: `pip install kaggle`, place your API token in `~/.kaggle/kaggle.json`, then `kaggle datasets download -d <owner>/<dataset-slug>`.
3. Keep the files **outside the repository** (or in a git-ignored folder) – real resumes contain personal data.

Kaggle data is not required to run, test or deploy the application.
