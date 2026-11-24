"""Module 1 - resume section identification and information extraction.

Combines heading rules, regular expressions and spaCy NER. Nothing is ever
invented: a field that cannot be found is returned as ``None`` / empty.
"""
import re

from .text_preprocessor import (
    clean_text,
    get_nlp,
    has_statistical_model,
    is_bullet,
    strip_bullet,
)

# Canonical section -> heading phrases (normalised: lower-case, '&' -> 'and').
SECTION_SYNONYMS = {
    "summary": ["summary", "professional summary", "profile", "profile summary", "objective",
                "career objective", "about me", "professional profile", "career summary",
                "personal statement", "executive summary"],
    "education": ["education", "academic background", "academic qualifications", "educational qualifications",
                  "educational qualification", "qualifications", "academics", "education details",
                  "academic details", "education and training", "academic profile"],
    "skills": ["skills", "technical skills", "core skills", "key skills", "technologies", "technical proficiency",
               "tools and technologies", "skill set", "skillset", "core competencies", "competencies",
               "technical expertise", "programming languages", "technical skills and tools", "it skills",
               "skills and tools", "technology stack", "tech stack", "areas of expertise"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "technical projects",
                 "project experience", "project work", "selected projects", "major projects", "project"],
    "experience": ["experience", "work experience", "professional experience", "employment history",
                   "work history", "employment", "relevant experience", "industry experience"],
    "internships": ["internship", "internships", "internship experience", "industrial training",
                    "industrial experience", "training", "training and internships", "internships and training"],
    "certifications": ["certifications", "certificates", "certification", "licenses and certifications",
                       "courses", "online courses", "courses and certifications", "certifications and courses",
                       "trainings and certifications", "professional certifications"],
    "achievements": ["achievements", "awards", "honors", "honours", "accomplishments", "awards and achievements",
                     "honors and awards", "achievements and awards", "awards and honors"],
    "activities": ["extracurricular activities", "extra curricular activities", "extra-curricular activities",
                   "activities", "positions of responsibility", "leadership", "volunteering",
                   "volunteer experience", "co-curricular activities"],
    "other": ["hobbies", "interests", "languages", "languages known", "publications", "references",
              "declaration", "personal details", "personal information", "strengths"],
}

SECTION_LABELS = {
    "summary": "Summary / Objective", "education": "Education", "skills": "Skills", "projects": "Projects",
    "experience": "Work Experience", "internships": "Internships", "certifications": "Certifications",
    "achievements": "Achievements", "activities": "Activities", "other": "Other",
}

_HEADING_LOOKUP = {phrase: section for section, phrases in SECTION_SYNONYMS.items() for phrase in phrases}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_CANDIDATE_RE = re.compile(r"(?<![\w/])\+?\(?\d[\d\s().\-]{8,17}\d(?![\w/])")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:[a-z]{2,3}\.)?linkedin\.com/(?:in|pub)/[A-Za-z0-9_\-%]+/?", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_\-]+/?", re.I)
URL_RE = re.compile(r"(?:https?://|www\.)[^\s|,;]+|\b[a-z0-9\-]+\.(?:dev|io|me|tech|site|netlify\.app|vercel\.app|github\.io)\b[^\s|,;]*", re.I)

DEGREE_RE = re.compile(
    r"\b(b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bsc|b\.?\s?c\.?\s?a|bca|m\.?\s?c\.?\s?a|mca|m\.?\s?tech|m\.?\s?e\b|"
    r"m\.?\s?sc|msc|mba|bba|b\.?\s?com|m\.?\s?com|ph\.?\s?d|bachelor(?:'?s)?|master(?:'?s)?|diploma|"
    r"associate degree|b\.?\s?s\b|m\.?\s?s\b|b\.?\s?a\b|m\.?\s?a\b|pre-university|puc|"
    r"higher secondary|senior secondary|hsc|ssc|class\s+(?:xii|x|12|10)(?:th)?|12th|10th)",
    re.I,
)
INSTITUTION_RE = re.compile(
    r"\b(university|college|institute|institution|school|academy|polytechnic|iit|nit|iiit|bits|vit)\b", re.I
)
YEAR_RE = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")
GRADE_RE = re.compile(
    r"\b(c?gpa|sgpa|cpi|percentage|grade|aggregate)\b\s*[:\-]?\s*\d|\b\d{1,2}(?:\.\d{1,2})?\s*%|"
    r"\b\d\.\d{1,2}\s*/\s*(?:10|4)(?:\.0)?\b|\bfirst class\b|\bdistinction\b",
    re.I,
)
FIELD_RE = re.compile(
    r"\b(computer science|information technology|information science|electronics|electrical|mechanical|civil|"
    r"data science|artificial intelligence|statistics|mathematics|physics|commerce|business|economics|"
    r"computer applications|software engineering|engineering|science)\b",
    re.I,
)
COURSEWORK_RE = re.compile(r"\b(relevant )?course\s?work\b|\brelevant courses\b", re.I)
INTERN_RE = re.compile(r"\bintern(ship)?s?\b", re.I)
DATE_RANGE_RE = re.compile(
    r"((jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?(19|20)\d{2}\s*(-|–|to)\s*"
    r"(((jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?(19|20)\d{2}|present|current|now)",
    re.I,
)
METRIC_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent\b|x\b|\+|k\b|users\b|customers\b|clients\b|records\b|rows\b|"
    r"students\b|hours\b|minutes\b|seconds\b|ms\b|requests\b|transactions\b|downloads\b|members\b|"
    r"teams?\b|people\b|images\b|samples\b|datasets?\b|reports?\b|dashboards?\b|services\b|servers\b|"
    r"applications?\b|pages\b|lakh\b|million\b|crore\b)",
    re.I,
)

ACTION_VERBS = {
    "developed", "built", "designed", "implemented", "created", "led", "managed", "analyzed", "analysed",
    "optimized", "optimised", "automated", "deployed", "improved", "reduced", "increased", "engineered",
    "collaborated", "integrated", "trained", "evaluated", "migrated", "configured", "maintained", "delivered",
    "launched", "architected", "visualized", "visualised", "cleaned", "wrote", "tested", "achieved",
    "coordinated", "established", "streamlined", "researched", "presented", "contributed", "programmed",
    "modeled", "modelled", "predicted", "scraped", "monitored", "provisioned", "containerized", "secured",
    "refactored", "debugged", "documented", "mentored", "organized", "organised", "conducted", "generated",
}
_ROLE_WORDS = {"engineer", "developer", "analyst", "scientist", "intern", "student", "manager", "designer",
               "consultant", "resume", "curriculum", "vitae", "architect", "administrator"}


# ---------------------------------------------------------------- headings
def _normalise_heading(line: str) -> str:
    text = line.lower().replace("&", " and ")
    text = re.sub(r"[^a-z\- ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_heading(line: str, docx_headings=frozenset()) -> tuple:
    """Return (section, inline_content) if ``line`` is a section heading, else (None, None)."""
    raw = line.strip()
    if not raw or is_bullet(raw) or len(raw) > 60:
        return None, None

    # "Skills: Python, SQL" -> heading with inline content
    inline = re.match(r"^([A-Za-z &/\-]{3,40}?)\s*[:|]\s*(.+)$", raw)
    if inline:
        key = _normalise_heading(inline.group(1))
        if key in _HEADING_LOOKUP:
            return _HEADING_LOOKUP[key], inline.group(2).strip()

    if len(raw.split()) > 6:
        return None, None
    key = _normalise_heading(raw)
    if key in _HEADING_LOOKUP:
        return _HEADING_LOOKUP[key], None

    # A heading-styled line ("TECHNICAL SKILLS & TOOLS", "Projects:") that contains a known phrase.
    looks_like_heading = raw.isupper() or raw.endswith(":") or raw in docx_headings
    if looks_like_heading:
        best = None
        for phrase, section in _HEADING_LOOKUP.items():
            if re.search(rf"\b{re.escape(phrase)}\b", key) and (best is None or len(phrase) > len(best[0])):
                best = (phrase, section)
        if best and len(key.split()) - len(best[0].split()) <= 3:
            return best[1], None
    return None, None


def split_sections(text: str, docx_headings=()) -> dict:
    """Split cleaned resume text into canonical sections."""
    docx_headings = frozenset(h.strip() for h in docx_headings)
    lines = text.split("\n")
    header_lines, sections, order, headings_found, duplicates = [], {}, [], [], []
    current = None

    for line in lines:
        section, inline = match_heading(line, docx_headings)
        # "Languages: Python, SQL" or "Programming Languages: ..." inside a section is a
        # sub-label, not a new section.
        if inline and current is not None and (section == current or section == "other"):
            section = None
        if section:
            headings_found.append(line.strip().rstrip(":"))
            if section in sections and section != "other":
                duplicates.append(section)
            else:
                sections.setdefault(section, {"heading": line.strip().rstrip(":"), "lines": []})
                if section not in order:
                    order.append(section)
            current = section
            if inline:
                sections[current]["lines"].append(inline)
            continue
        if current is None:
            if line.strip():
                header_lines.append(line.strip())
        elif line.strip():
            sections[current]["lines"].append(line.strip())

    for data in sections.values():
        data["content"] = "\n".join(data["lines"])
        data["word_count"] = len(data["content"].split())

    # Unrecognised, heading-like lines (ALL CAPS, short) after the header.
    unrecognised = [
        l.strip() for l in lines
        if l.strip().isupper() and 1 <= len(l.split()) <= 4 and l.strip() not in headings_found
        and not EMAIL_RE.search(l) and l.strip() not in header_lines[:2]
    ]
    return {
        "header": "\n".join(header_lines),
        "sections": sections,
        "order": order,
        "headings_found": headings_found,
        "duplicate_sections": sorted(set(duplicates)),
        "unrecognised_headings": unrecognised[:10],
    }


# ---------------------------------------------------------------- contact / name
def extract_contact(text: str) -> dict:
    emails = EMAIL_RE.findall(text)
    phone = None
    for cand in PHONE_CANDIDATE_RE.findall(text):
        digits = re.sub(r"\D", "", cand)
        # Exclude date ranges such as "2019 - 2023" (8 digits) and long IDs.
        if 10 <= len(digits) <= 13 and not DATE_RANGE_RE.search(cand):
            phone = cand.strip()
            break
    linkedin = LINKEDIN_RE.search(text)
    github = GITHUB_RE.search(text)
    other_urls = [
        u for u in URL_RE.findall(text)
        if "linkedin.com" not in u.lower() and "github.com" not in u.lower() and "@" not in u
    ]
    return {
        "email": emails[0] if emails else None,
        "phone": phone,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
        "portfolio": other_urls[0] if other_urls else None,
    }


def _plausible_name(line: str) -> bool:
    line = line.strip()
    if not line or EMAIL_RE.search(line) or re.search(r"\d|https?:|www\.|\|", line):
        return False
    words = line.replace(".", " ").split()
    if not 2 <= len(words) <= 4:
        return False
    if any(w.lower() in _ROLE_WORDS for w in words):
        return False
    if match_heading(line)[0]:
        return False
    return all(re.fullmatch(r"[A-Za-z][A-Za-z'\-]*", w) for w in words)


def extract_name(header: str, full_text: str) -> dict:
    """Candidate name using spaCy NER where available, else a layout heuristic."""
    candidates = [l for l in (header or full_text).split("\n")[:6] if l.strip()]
    plausible = [l.strip() for l in candidates if _plausible_name(l)]

    if has_statistical_model() and candidates:
        doc = get_nlp()("\n".join(candidates))
        for ent in doc.ents:
            if ent.label_ == "PERSON" and _plausible_name(ent.text):
                return {"value": ent.text.strip(), "method": "spaCy named-entity recognition"}
        # NER often misses ALL-CAPS names; retry with title case.
        doc = get_nlp()("\n".join(c.title() for c in candidates))
        for ent in doc.ents:
            if ent.label_ == "PERSON" and _plausible_name(ent.text):
                return {"value": ent.text.strip(), "method": "spaCy named-entity recognition"}

    if plausible:
        return {"value": plausible[0], "method": "header heuristic"}
    return {"value": None, "method": None}


# ---------------------------------------------------------------- section details
def analyse_education(section_text: str, full_text: str) -> dict:
    scope = section_text or ""
    degrees = sorted({m.group(0).strip() for m in DEGREE_RE.finditer(scope)}, key=str.lower)
    institutions = [l for l in scope.split("\n") if INSTITUTION_RE.search(l)]
    years = sorted(set(YEAR_RE.findall(scope)))
    result = {
        "section_present": bool(section_text),
        "degrees": degrees[:5],
        "institutions": [strip_bullet(i)[:120] for i in institutions[:4]],
        "years": years,
        "has_grade": bool(GRADE_RE.search(scope)),
        "has_field_of_study": bool(FIELD_RE.search(scope)),
        "has_coursework": bool(COURSEWORK_RE.search(scope)),
        "degree_mentioned_elsewhere": False,
    }
    if not section_text and DEGREE_RE.search(full_text):
        result["degree_mentioned_elsewhere"] = True
    return result


def _count_entries(section_text: str) -> int:
    """Approximate number of entries (e.g. projects) in a section."""
    lines = [l for l in section_text.split("\n") if l.strip()]
    titles = [
        l for l in lines
        if not is_bullet(l) and len(l.split()) <= 14 and not l.rstrip().endswith(".")
    ]
    if titles:
        return len(titles)
    bullets = [l for l in lines if is_bullet(l)]
    return max(1, len(bullets) // 3) if bullets else (1 if lines else 0)


def count_action_verbs(text: str) -> list:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return sorted(words & ACTION_VERBS)


def find_metrics(text: str) -> list:
    return [m.group(0).strip() for m in METRIC_RE.finditer(text)]


def analyse_projects(section_text: str, experience_text: str) -> dict:
    text = section_text or ""
    return {
        "section_present": bool(section_text),
        "entry_count": _count_entries(text) if text else 0,
        "word_count": len(text.split()),
        "action_verbs": count_action_verbs(text),
        "metrics": find_metrics(text)[:10],
        "mentioned_in_experience": bool(re.search(r"\bproject", experience_text or "", re.I)),
    }


def analyse_experience(sections: dict, full_text: str) -> dict:
    exp = sections.get("experience", {}).get("content", "")
    intern = sections.get("internships", {}).get("content", "")
    combined = f"{exp}\n{intern}"
    return {
        "experience_section_present": bool(exp),
        "internship_section_present": bool(intern),
        "internship_detected": bool(intern) or bool(INTERN_RE.search(exp)),
        "internship_mentioned_anywhere": bool(INTERN_RE.search(full_text)),
        "entry_count": _count_entries(combined) if combined.strip() else 0,
        "date_ranges": len(DATE_RANGE_RE.findall(combined)),
        "action_verbs": count_action_verbs(combined),
        "word_count": len(combined.split()),
    }


def _list_items(section_text: str, limit: int = 10) -> list:
    items = [strip_bullet(l) for l in section_text.split("\n") if l.strip()]
    return [i[:150] for i in items[:limit]]


# ---------------------------------------------------------------- orchestrator
def extract_resume_information(raw_text: str, docx_headings=()) -> dict:
    """Run the full Module 1 information-extraction step on raw document text."""
    text = clean_text(raw_text)
    split = split_sections(text, docx_headings)
    sections = split["sections"]

    def content(name):
        return sections.get(name, {}).get("content", "")

    contact = extract_contact(text)
    name = extract_name(split["header"], text)
    bullet_lines = sum(1 for l in text.split("\n") if is_bullet(l))
    body_without_header = "\n".join(
        content(s) for s in ("experience", "internships", "projects", "achievements", "summary", "activities")
    )

    return {
        "clean_text": text,
        "candidate": {
            "name": name["value"],
            "name_method": name["method"],
            **contact,
        },
        "section_order": split["order"],
        "sections": {
            key: {"heading": val["heading"], "content": val["content"], "word_count": val["word_count"]}
            for key, val in sections.items()
        },
        "headings_found": split["headings_found"],
        "duplicate_sections": split["duplicate_sections"],
        "unrecognised_headings": split["unrecognised_headings"],
        "header_text": split["header"][:500],
        "summary": content("summary")[:1000] or None,
        "education": analyse_education(content("education"), text),
        "projects": analyse_projects(content("projects"), content("experience")),
        "experience": analyse_experience(sections, text),
        "certifications": _list_items(content("certifications")),
        "certification_mentioned": bool(re.search(r"\bcertif(ied|icate|ication)", text, re.I)),
        "achievements": _list_items(content("achievements")),
        "metrics": find_metrics(body_without_header)[:15],
        "bullet_line_count": bullet_lines,
        "line_count": len([l for l in text.split("\n") if l.strip()]),
    }
