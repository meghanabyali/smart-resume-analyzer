"""Generate SYNTHETIC sample resumes (PDF + DOCX) into data/sample_resumes/.

All people, contact details, institutions and companies below are fictional
and were written for this project. Emails use the reserved example.com domain.

Usage:  python scripts/generate_samples.py
"""
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sample_resumes"

# Each resume: name, contact line, list of (heading, [lines]) - lines starting with "- " are bullets.
SAMPLES = {
    "data_analyst_strong": {
        "format": "pdf", "role": "data_analyst", "quality": "strong",
        "name": "Ananya Rao",
        "contact": "ananya.rao@example.com | +91 98765 43210 | linkedin.com/in/ananya-rao-sample | github.com/ananya-sample",
        "sections": [
            ("Professional Summary", ["Final-year Computer Science student and aspiring Data Analyst with hands-on "
                                      "experience in SQL, Python and Power BI, turning raw data into business insights."]),
            ("Education", ["B.Tech in Computer Science and Engineering", "Sample Institute of Technology, Bengaluru | 2021 - 2025",
                           "CGPA: 8.7/10 | Relevant coursework: Statistics, Database Systems, Data Mining"]),
            ("Technical Skills", ["Languages: Python, SQL, R programming",
                                  "Libraries: Pandas, NumPy, Matplotlib, Seaborn",
                                  "Tools: Excel (pivot tables, VLOOKUP), Power BI, Tableau, Git, Jupyter",
                                  "Concepts: Data Cleaning, Data Visualization, Statistics, ETL, Data Modeling, Data Analysis"]),
            ("Projects", ["Retail Sales Dashboard",
                          "- Built an interactive Power BI dashboard on 50,000 sales records to track revenue by region and category.",
                          "- Wrote SQL queries with joins and window functions; reduced manual reporting time by 40%.",
                          "Customer Churn Analysis",
                          "- Performed data cleaning and exploratory data analysis in Python (Pandas, Seaborn) on 7,000 customer records.",
                          "- Applied hypothesis testing to identify 3 key churn drivers and presented findings to 20 peers.",
                          "COVID-19 Data Pipeline",
                          "- Developed an ETL data pipeline in Python that loads daily data into a MySQL star schema."]),
            ("Internship Experience", ["Data Analyst Intern, Example Analytics Pvt. Ltd. | Jun 2024 - Aug 2024",
                                       "- Automated weekly Excel reports with Python, saving 6 hours per week.",
                                       "- Analyzed marketing campaign data and visualized results in Tableau for 4 teams."]),
            ("Certifications", ["Google Data Analytics Professional Certificate (2024)", "Microsoft Power BI Data Analyst - PL-300 (2024)"]),
            ("Achievements", ["Winner, inter-college Datathon 2023 (out of 120 teams)"]),
        ],
    },
    "data_analyst_average": {
        "format": "docx", "role": "data_analyst", "quality": "average",
        "name": "Rohit Menon",
        "contact": "rohit.menon@example.com | 9876501234",
        "sections": [
            ("Objective", ["To obtain a challenging position in a reputed organization where I can use my skills."]),
            ("Education", ["Bachelor of Science (Statistics), Sample Arts and Science College, 2020 - 2023"]),
            ("Skills", ["Excel, Python, communication, teamwork, problem solving"]),
            ("Projects", ["Sales analysis", "- Analyzed sales data in Excel and made charts."]),
            ("Hobbies", ["Cricket, music"]),
        ],
    },
    "web_developer_strong": {
        "format": "docx", "role": "web_developer", "quality": "strong",
        "name": "Kavya Iyer",
        "contact": "kavya.iyer@example.com | +91 91234 56780 | linkedin.com/in/kavya-iyer-sample | github.com/kavya-sample | kavya-sample.netlify.app",
        "sections": [
            ("Summary", ["Full-stack web developer and final-year IT student who builds responsive, accessible web "
                         "applications with React, Node.js and REST APIs."]),
            ("Technical Skills", ["Frontend: HTML5, CSS3, JavaScript (ES6), React, Bootstrap, Tailwind CSS",
                                  "Backend: Node.js, Express.js, REST API, MongoDB, MySQL, SQL",
                                  "Tools: Git, GitHub Actions, Postman, Docker"]),
            ("Projects", ["Campus Event Portal",
                          "- Developed a responsive design React frontend and Node.js/Express REST API used by 1,200 students.",
                          "- Implemented JWT authentication and MySQL storage; reduced page load time by 35%.",
                          "Expense Tracker PWA",
                          "- Built a mobile-first progressive web app with JavaScript and IndexedDB; 500+ downloads.",
                          "Portfolio Website",
                          "- Designed and deployed a portfolio with Bootstrap and CI/CD via GitHub Actions."]),
            ("Experience", ["Web Development Intern, Example Web Studio | May 2024 - Jul 2024",
                            "- Integrated third-party APIs into 3 client websites and fixed 40+ frontend bugs.",
                            "- Collaborated with designers to convert Figma mockups into React components."]),
            ("Education", ["B.E. in Information Technology", "Sample College of Engineering, Pune | 2021 - 2025 | CGPA 8.9/10"]),
            ("Certifications", ["freeCodeCamp Responsive Web Design (2023)", "Meta Front-End Developer Professional Certificate (2024)"]),
        ],
    },
    "web_developer_incomplete": {
        "format": "pdf", "role": "web_developer", "quality": "incomplete",
        "name": "Arjun Das",
        "contact": "arjun.das@example.com",
        "sections": [
            ("Skills", ["HTML, CSS, JavaScript"]),
            ("Projects", ["Personal website made using HTML and CSS."]),
            ("Education", ["BCA, 2024"]),
        ],
    },
    "ai_engineer_strong": {
        "format": "pdf", "role": "ai_engineer", "quality": "strong",
        "name": "Meera Krishnan",
        "contact": "meera.k@example.com | +91 99887 76655 | linkedin.com/in/meera-krishnan-sample | github.com/meera-sample",
        "sections": [
            ("Profile", ["AI Engineer and M.Tech student specialising in machine learning and NLP, experienced in building, "
                         "evaluating and deploying models with Scikit-learn, TensorFlow and PyTorch."]),
            ("Education", ["M.Tech in Artificial Intelligence, Sample University | 2023 - 2025 | CGPA 9.1/10",
                           "B.Tech in Computer Science, Sample Institute of Engineering | 2019 - 2023"]),
            ("Skills", ["Python, SQL, Git, Linux",
                        "Machine Learning, Deep Learning, NLP, Computer Vision",
                        "Scikit-learn, TensorFlow, Keras, PyTorch, spaCy, NLTK, Pandas, NumPy",
                        "Data Preprocessing, Feature Engineering, Model Evaluation (cross-validation, F1-score)",
                        "Flask, FastAPI, Docker, API Integration"]),
            ("Projects", ["Resume Classifier",
                          "- Trained a TF-IDF + logistic regression model on 2,400 resumes achieving 91% accuracy and 0.89 F1-score.",
                          "- Deployed the model as a FastAPI service with Docker, serving 200 requests per minute.",
                          "Medical Image Classification",
                          "- Fine-tuned a CNN in PyTorch on 10,000 chest X-ray images; improved recall by 12% using augmentation.",
                          "Customer Support Chatbot",
                          "- Built an intent-classification chatbot using spaCy and integrated it with a Flask web app."]),
            ("Work Experience", ["Machine Learning Intern, Example AI Labs | Jan 2024 - Jun 2024",
                                 "- Implemented data preprocessing pipelines that reduced training data errors by 30%.",
                                 "- Evaluated 5 model variants with cross-validation and documented results for the team."]),
            ("Certifications", ["DeepLearning.AI Machine Learning Specialization (2023)", "TensorFlow Developer Certificate (2024)"]),
            ("Publications", ["Short paper on resume text classification, Sample Student Conference 2024"]),
        ],
    },
    "ai_engineer_poorly_structured": {
        "format": "docx", "role": "ai_engineer", "quality": "poorly_structured",
        "name": "",
        "contact": "",
        "sections": [
            ("", ["Vikram Shetty vikram.shetty@example.com I am a hardworking student interested in AI and I know python "
                  "and machine learning and did a project on house price prediction using linear regression and also "
                  "another one on movie recommendation, I studied at Sample Engineering College and completed BE in "
                  "2024, I am a quick learner and team player and want to work in a good company where I can grow my "
                  "career and learn new technologies like deep learning and tensorflow and contribute to the "
                  "organization goals with dedication and sincerity. I also like reading and playing chess."]),
        ],
    },
    "cloud_engineer_average": {
        "format": "pdf", "role": "cloud_engineer", "quality": "average",
        "name": "Sanjay Kulkarni",
        "contact": "sanjay.kulkarni@example.com | +91 90080 70060 | linkedin.com/in/sanjay-k-sample",
        "sections": [
            ("Summary", ["Computer Science graduate interested in cloud infrastructure and DevOps."]),
            ("Skills", ["AWS (EC2, S3), Linux, Docker, Git, Python, Bash scripting, Networking basics"]),
            ("Projects", ["Static Website Hosting on AWS",
                          "- Deployed a static website on AWS S3 with CloudFront and configured IAM users.",
                          "Dockerized Flask App",
                          "- Containerized a Flask application with Docker and ran it on an Ubuntu EC2 instance."]),
            ("Education", ["B.E. Computer Science, Sample Technological University | 2020 - 2024 | 7.6 CGPA"]),
            ("Certifications", ["AWS Certified Cloud Practitioner (2024)"]),
        ],
    },
    "cloud_engineer_incomplete": {
        "format": "docx", "role": "cloud_engineer", "quality": "incomplete",
        "name": "Neha Joshi",
        "contact": "+91 98450 12345",
        "sections": [
            ("Education", ["Diploma in Computer Engineering, Sample Polytechnic, 2023"]),
            ("Experience", ["IT Support Assistant at Example Services",
                            "- Helped users with computer problems and installed software."]),
        ],
    },
}


def _write_pdf(path: Path, sample: dict) -> None:
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("n", parent=styles["Title"], fontSize=18, spaceAfter=2)
    contact_style = ParagraphStyle("c", parent=styles["Normal"], fontSize=9, alignment=1)
    h = ParagraphStyle("h", parent=styles["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=3)
    body = ParagraphStyle("b", parent=styles["Normal"], fontSize=10, leading=13)
    story = []
    if sample["name"]:
        story.append(Paragraph(sample["name"], name_style))
    if sample["contact"]:
        story.append(Paragraph(sample["contact"], contact_style))
    for heading, lines in sample["sections"]:
        if heading:
            story.append(Paragraph(heading.upper(), h))
        bullets = []
        for line in lines + [None]:
            if line is not None and line.startswith("- "):
                bullets.append(ListItem(Paragraph(line[2:], body), leftIndent=10))
                continue
            if bullets:
                story.append(ListFlowable(bullets, bulletType="bullet", start="•", leftIndent=12))
                bullets = []
            if line is not None:
                story.append(Paragraph(line, body))
        story.append(Spacer(1, 2))
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=15 * mm, bottomMargin=15 * mm, title="Sample Resume").build(story)


def _write_docx(path: Path, sample: dict) -> None:
    doc = Document()
    doc.styles["Normal"].font.size = Pt(10.5)
    if sample["name"]:
        doc.add_heading(sample["name"], level=0)
    if sample["contact"]:
        doc.add_paragraph(sample["contact"])
    for heading, lines in sample["sections"]:
        if heading:
            doc.add_heading(heading, level=1)
        for line in lines:
            if line.startswith("- "):
                doc.add_paragraph(line[2:], style="List Bullet")
            else:
                doc.add_paragraph(line)
    doc.save(str(path))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, sample in SAMPLES.items():
        path = OUT / f"{key}.{sample['format']}"
        (_write_pdf if sample["format"] == "pdf" else _write_docx)(path, sample)
        print(f"wrote {path.relative_to(ROOT)}  ({sample['role']}, {sample['quality']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
