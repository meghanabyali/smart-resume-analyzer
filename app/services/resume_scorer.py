"""Module 2 - rule-based resume score (0-100) across six parameters.

Each ``calculate_*`` function is independent and returns a dict:
    {key, label, score, max_score, evidence[], missing[], explanation}
Sub-checks are scaled to the configured maximum, so the weights in
``Config.RESUME_SCORE_WEIGHTS`` can be changed without touching this code.
"""
from .section_extractor import SECTION_LABELS

DEFAULT_WEIGHTS = {"structure": 20, "skills": 20, "education": 15, "projects": 15, "contact": 15, "completeness": 15}
DEFAULT_CATEGORIES = [(85, "Excellent"), (70, "Good"), (50, "Needs Improvement"), (0, "Significant Improvement Needed")]

MAIN_SECTIONS = ("summary", "education", "skills", "projects", "experience", "internships",
                 "certifications", "achievements")


class _Checks:
    """Accumulates sub-check points, evidence and gaps for one parameter."""

    def __init__(self, key, label, max_score):
        self.key, self.label, self.max_score = key, label, max_score
        self.points, self.possible = 0.0, 0.0
        self.evidence, self.missing = [], []

    def add(self, awarded, possible, evidence=None, missing=None):
        self.points += awarded
        self.possible += possible
        if evidence:
            self.evidence.append(evidence)
        if missing:
            self.missing.append(missing)

    def result(self, explanation):
        score = round(self.max_score * self.points / self.possible, 1) if self.possible else 0.0
        score = max(0.0, min(float(self.max_score), score))
        return {
            "key": self.key,
            "label": self.label,
            "score": score,
            "max_score": self.max_score,
            "percentage": round(100 * score / self.max_score) if self.max_score else 0,
            "evidence": self.evidence,
            "missing": self.missing,
            "explanation": explanation,
        }


# ------------------------------------------------------------------ 1. structure
def calculate_structure_score(info: dict, document: dict, max_score: float = 20) -> dict:
    c = _Checks("structure", "Resume Structure", max_score)
    found = [s for s in info["section_order"] if s in MAIN_SECTIONS]

    # Recognisable section headings (6)
    pts = min(6, 1.5 * len(found))
    c.add(pts, 6,
          f"{len(found)} standard section heading(s) detected: "
          + ", ".join(SECTION_LABELS[s] for s in found) if found else None,
          None if len(found) >= 4 else "Fewer than 4 clearly labelled standard sections")

    # Logical organisation (4): identity at the top, no repeated sections
    header = info.get("header_text", "")
    identity_on_top = bool(info["candidate"].get("name") or info["candidate"].get("email")) and bool(header)
    c.add(2 if identity_on_top else 0, 2,
          "Name/contact details appear before the first section" if identity_on_top else None,
          None if identity_on_top else "Name and contact details are not at the top of the resume")
    no_dupes = not info.get("duplicate_sections")
    c.add(2 if no_dupes else 0, 2,
          "No section is repeated" if no_dupes else None,
          None if no_dupes else "Repeated section(s): " + ", ".join(info["duplicate_sections"]))

    # Readable extracted text (4)
    text = info["clean_text"]
    alpha_ratio = sum(ch.isalpha() for ch in text) / max(1, len(text.replace(" ", "").replace("\n", "")))
    odd_chars = sum(1 for ch in text if ch == "�" or (ord(ch) > 0x2fff and not ch.isalpha()))
    readable = alpha_ratio >= 0.6 and odd_chars <= max(3, len(text) // 200)
    c.add(3 if readable else 1, 3,
          f"Text extracted cleanly ({round(alpha_ratio * 100)}% alphabetic characters)" if readable else None,
          None if readable else "Extracted text contains many unreadable or non-text characters")

    # Reasonable length (7)
    words, pages = document["word_count"], document["page_count"]
    if 250 <= words <= 1100 and pages <= 2:
        c.add(7, 7, f"Appropriate length: {words} words, {pages} page(s)")
    elif 150 <= words < 250 or 1100 < words <= 1600 or pages == 3:
        c.add(4, 7, f"Length: {words} words, {pages} page(s)",
              "Length is outside the typical 1-2 page / 250-1100 word range")
    elif 80 <= words < 150:
        c.add(2, 7, f"Length: {words} words", "The resume is very short (250+ words is typical)")
    else:
        c.add(0, 7, None, f"Length ({words} words, {pages} page(s)) is far from the typical range")

    return c.result(
        "Measures whether a reader or ATS can recognise standard sections, find your identity at the "
        "top, read the text cleanly and scan a document of reasonable length."
    )


# ------------------------------------------------------------------ 2. skills
def calculate_skills_score(info: dict, detected: dict, skills_in_section: dict, role_match: dict,
                           max_score: float = 20) -> dict:
    c = _Checks("skills", "Skills Section", max_score)
    has_section = "skills" in info["sections"]
    c.add(5 if has_section else 0, 5,
          f"Dedicated skills section: '{info['sections']['skills']['heading']}'" if has_section else None,
          None if has_section else "No dedicated skills section")

    n = len(detected)
    pts = 6 if n >= 12 else 5 if n >= 8 else 3 if n >= 5 else 1 if n >= 2 else 0
    c.add(pts, 6, f"{n} identifiable technical skill(s) found" if n else None,
          None if n >= 8 else "Few identifiable technical skills (8+ recommended)")

    coverage = role_match["match_percentage"] / 100
    rel = round(6 * min(1.0, coverage / 0.6), 1)
    c.add(rel, 6,
          f"{len(role_match['matched'])}/{len(role_match['reference_keywords'])} role keywords present" if role_match["matched"] else None,
          None if coverage >= 0.6 else "Less than 60% of the selected role's reference keywords present")

    in_section = len(skills_in_section)
    if has_section and in_section >= 5:
        c.add(3, 3, f"{in_section} skills clearly listed inside the skills section")
    elif has_section and in_section >= 1:
        c.add(1.5, 3, f"{in_section} skill(s) listed in the skills section",
              "Skills section lists few recognisable technical skills")
    else:
        c.add(0, 3, None, "Skills are not clearly presented in a list")

    return c.result(
        "Rewards a dedicated, scannable skills section with a healthy number of recognisable technical "
        "skills that are relevant to the selected role."
    )


# ------------------------------------------------------------------ 3. education
def calculate_education_score(info: dict, max_score: float = 15) -> dict:
    c = _Checks("education", "Education Details", max_score)
    edu = info["education"]
    c.add(5 if edu["section_present"] else 0, 5,
          "Education section present" if edu["section_present"] else None,
          None if edu["section_present"] else (
              "No labelled education section (a degree is mentioned elsewhere)"
              if edu["degree_mentioned_elsewhere"] else "No education section"))
    c.add(4 if edu["degrees"] else 0, 4,
          "Degree/qualification: " + ", ".join(edu["degrees"][:3]) if edu["degrees"] else None,
          None if edu["degrees"] else "Degree or qualification name not found")
    c.add(3 if edu["institutions"] else 0, 3,
          "Institution: " + edu["institutions"][0] if edu["institutions"] else None,
          None if edu["institutions"] else "Institution name not found")
    c.add(2 if edu["years"] else 0, 2,
          "Year(s): " + ", ".join(edu["years"]) if edu["years"] else None,
          None if edu["years"] else "Graduation year or duration not found")
    detail = edu["has_grade"] or edu["has_field_of_study"] or edu["has_coursework"]
    kinds = [k for k, v in (("grade/CGPA", edu["has_grade"]), ("field of study", edu["has_field_of_study"]),
                            ("coursework", edu["has_coursework"])) if v]
    c.add(1 if detail else 0, 1, "Academic details: " + ", ".join(kinds) if detail else None,
          None if detail else "No field of study, grade or coursework mentioned (optional)")
    return c.result(
        "Checks for a labelled education section with degree, institution and dates. Grades are optional "
        "and only contribute a small 'academic details' point together with field of study or coursework."
    )


# ------------------------------------------------------------------ 4. projects
def calculate_projects_score(info: dict, project_skills: dict, max_score: float = 15) -> dict:
    c = _Checks("projects", "Projects Section", max_score)
    p = info["projects"]
    c.add(4 if p["section_present"] else 0, 4, "Projects section present" if p["section_present"] else None,
          None if p["section_present"] else "No projects section")

    n = p["entry_count"]
    if n >= 2:
        c.add(3, 3, f"About {n} project entries")
    elif n == 1:
        c.add(2, 3, "1 project entry", "Only one project described (2+ recommended)")
    elif p["mentioned_in_experience"]:
        c.add(1, 3, "Projects are mentioned within experience", "No separate project entries")
    else:
        c.add(0, 3, None, "No project entries")

    w = p["word_count"]
    pts = 3 if w >= 60 else 2 if w >= 30 else 1 if w >= 15 else 0
    c.add(pts, 3, f"Project descriptions total {w} words" if w else None,
          None if w >= 60 else "Project descriptions are brief")

    t = len(project_skills)
    c.add(min(3, t), 3, "Technologies named in projects: " + ", ".join(sorted(project_skills)[:8]) if t else None,
          None if t >= 3 else "Few technologies named in project descriptions")

    v = p["action_verbs"]
    c.add(2 if len(v) >= 3 else 1 if v else 0, 2,
          "Contribution verbs: " + ", ".join(v[:6]) if v else None,
          None if len(v) >= 3 else "Contributions are not described with action verbs")
    return c.result(
        "Evaluates whether projects are present, described in enough detail, name the technologies used "
        "and explain your contribution with action verbs."
    )


# ------------------------------------------------------------------ 5. contact
def calculate_contact_score(info: dict, max_score: float = 15) -> dict:
    c = _Checks("contact", "Contact Information", max_score)
    cand = info["candidate"]
    c.add(5 if cand["email"] else 0, 5, f"Email: {cand['email']}" if cand["email"] else None,
          None if cand["email"] else "Email address not found")
    c.add(4 if cand["phone"] else 0, 4, f"Phone: {cand['phone']}" if cand["phone"] else None,
          None if cand["phone"] else "Phone number not found")
    c.add(3 if cand["name"] else 0, 3,
          f"Candidate name: {cand['name']} ({cand['name_method']})" if cand["name"] else None,
          None if cand["name"] else "Candidate name could not be identified")
    c.add(2 if cand["linkedin"] else 0, 2, "LinkedIn profile linked" if cand["linkedin"] else None,
          None if cand["linkedin"] else "No LinkedIn URL (optional)")
    has_work_link = cand["github"] or cand["portfolio"]
    c.add(1 if has_work_link else 0, 1,
          "GitHub/portfolio link: " + (cand["github"] or cand["portfolio"]) if has_work_link else None,
          None if has_work_link else "No GitHub or portfolio link (optional)")
    return c.result(
        "Email, phone and an identifiable name carry most of the weight. Profile links are optional and "
        "contribute only a small share."
    )


# ------------------------------------------------------------------ 6. completeness
def calculate_completeness_score(info: dict, document: dict, max_score: float = 15) -> dict:
    c = _Checks("completeness", "Resume Completeness", max_score)
    secs = info["sections"]

    has_summary = "summary" in secs and secs["summary"]["word_count"] >= 10
    c.add(3 if has_summary else 0, 3,
          f"Summary/objective ({secs['summary']['word_count']} words)" if has_summary else None,
          None if has_summary else "No professional summary or objective")

    exp = info["experience"]
    if exp["experience_section_present"] or exp["internship_detected"]:
        c.add(3, 3, "Work or internship experience documented")
    elif info["projects"]["entry_count"] >= 2:
        c.add(3, 3, "Practical work demonstrated through multiple projects")
    elif info["projects"]["entry_count"] == 1:
        c.add(2, 3, "Practical work shown through one project", "Limited practical experience evidence")
    else:
        c.add(0, 3, None, "No experience, internship or project evidence")

    m = len(info["metrics"])
    c.add(min(3, m), 3, "Quantified outcomes: " + ", ".join(info["metrics"][:4]) if m else None,
          None if m >= 3 else "Few measurable outcomes (numbers, %, scale)")

    w = document["word_count"]
    c.add(3 if w >= 350 else 2 if w >= 200 else 1 if w >= 100 else 0, 3, f"{w} words of content",
          None if w >= 350 else "Content is thin overall")

    present = [k for k in secs if k in MAIN_SECTIONS]
    filled = [k for k in present if secs[k]["word_count"] >= 5]
    empty = [SECTION_LABELS[k] for k in present if k not in filled]
    ratio = len(filled) / len(present) if present else 0
    c.add(round(3 * ratio, 1), 3,
          f"{len(filled)}/{len(present)} sections contain meaningful content" if present else None,
          None if not empty and present else ("Sections with little content: " + ", ".join(empty)
                                              if empty else "No standard sections to evaluate"))

    return c.result(
        "Checks that the essential information is present and sufficiently detailed. Optional sections such "
        "as certifications or internships are not penalised here - they appear only as suggestions."
    )


# ------------------------------------------------------------------ total
def categorise(score: float, categories=None) -> str:
    for threshold, label in categories or DEFAULT_CATEGORIES:
        if score >= threshold:
            return label
    return (categories or DEFAULT_CATEGORIES)[-1][1]


def calculate_total_resume_score(info, document, detected, skills_in_section, project_skills, role_match,
                                 weights=None, categories=None) -> dict:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    params = [
        calculate_structure_score(info, document, w["structure"]),
        calculate_skills_score(info, detected, skills_in_section, role_match, w["skills"]),
        calculate_education_score(info, w["education"]),
        calculate_projects_score(info, project_skills, w["projects"]),
        calculate_contact_score(info, w["contact"]),
        calculate_completeness_score(info, document, w["completeness"]),
    ]
    raw_total = sum(p["score"] for p in params)
    total = int(round(min(100, max(0, raw_total))))
    return {
        "total": total,
        "raw_total": round(raw_total, 1),
        "max_total": sum(p["max_score"] for p in params),
        "category": categorise(total, categories),
        "parameters": params,
    }
