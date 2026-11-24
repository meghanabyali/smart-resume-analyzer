"""Module 4 - Smart Feedback System (rule-based recommendation engine).

Every recommendation is triggered by a specific finding in the analysis, so
feedback differs from resume to resume. Recommendations about skills or
experience are always phrased conditionally ("If you have ...") - the system
never suggests claiming skills the candidate does not have.
"""
import re

from .section_extractor import SECTION_LABELS

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def _item(category, priority, title, issue, evidence, recommendation, explanation):
    return {
        "category": category,
        "priority": priority,
        "title": title,
        "issue": issue,
        "evidence": evidence,
        "recommendation": recommendation,
        "explanation": explanation,
    }


def _param(ctx, key):
    return next(p for p in ctx["resume_score"]["parameters"] if p["key"] == key)


# ------------------------------------------------------------------ structure / formatting
def generate_structure_feedback(ctx) -> list:
    info, doc, items = ctx["info"], ctx["document"], []
    structure = _param(ctx, "structure")
    found = [SECTION_LABELS[s] for s in info["section_order"]]
    pct = structure["score"] / structure["max_score"]

    if pct < 0.75:
        items.append(_item(
            "Resume Formatting", "High" if pct < 0.5 else "Medium", "Improve resume formatting",
            f"Resume structure scored {structure['score']:g}/{structure['max_score']}.",
            "Headings detected: " + (", ".join(found) if found else "none") + ". "
            + ("; ".join(structure["missing"]) if structure["missing"] else ""),
            "Use clear, standard section headings (Summary, Education, Skills, Projects, Experience) on their "
            "own lines, keep your name and contact details at the top, and list content under each heading.",
            "Recruiters and ATS parsers locate information by standard headings; unclear structure can cause "
            "content to be missed.",
        ))
    if doc.get("layout", {}).get("multi_column") or doc.get("layout", {}).get("table_count", 0) > 2:
        items.append(_item(
            "Resume Formatting", "Medium", "Use an ATS-friendly single-column layout",
            "The document uses a multi-column or table-based layout.",
            "Layout analysis: multi-column=%s, tables=%s" % (doc["layout"].get("multi_column"),
                                                           doc["layout"].get("table_count", 0)),
            "Consider a single-column layout without text inside tables or text boxes.",
            "Many parsers read columns and tables out of order, which can scramble sections.",
        ))
    if info.get("bullet_line_count", 0) < 3 and info["line_count"] > 10:
        items.append(_item(
            "Resume Formatting", "Low", "Use bullet points",
            "Few or no bullet points were detected.",
            f"{info.get('bullet_line_count', 0)} bullet line(s) across {info['line_count']} lines.",
            "Present responsibilities and achievements as short bullet points starting with an action verb.",
            "Bullet points make resumes faster to scan for both recruiters and ATS software.",
        ))
    words = doc["word_count"]
    if words > 1100 or doc["page_count"] > 2:
        items.append(_item(
            "Resume Formatting", "Low", "Shorten the resume",
            "The resume is longer than typical for a student or early-career candidate.",
            f"{words} words, {doc['page_count']} page(s).",
            "Aim for one page (two at most): remove outdated or less relevant details.",
            "Concise resumes are easier to scan in the few seconds a recruiter typically spends on a first pass.",
        ))
    if info.get("duplicate_sections"):
        items.append(_item(
            "Resume Organization", "Low", "Merge repeated sections",
            "The same section heading appears more than once.",
            "Repeated: " + ", ".join(SECTION_LABELS.get(s, s) for s in info["duplicate_sections"]),
            "Combine repeated sections into a single section.",
            "Repeated headings make the structure harder to follow and parse.",
        ))
    return items


# ------------------------------------------------------------------ skills
def generate_skills_feedback(ctx) -> list:
    info, items = ctx["info"], []
    detected, in_section = ctx["detected_skills"], ctx["skills_in_section"]
    if "skills" not in info["sections"]:
        items.append(_item(
            "Technical Skills", "High", "Add a technical skills section",
            "No dedicated skills section was detected.",
            f"{len(detected)} skill(s) were found scattered through the text: "
            + (", ".join(sorted(detected)[:8]) if detected else "none") + ".",
            "Add a 'Technical Skills' section grouping the tools, languages and frameworks you actually use.",
            "ATS keyword searches and recruiters look first at a skills section.",
        ))
    elif len(in_section) < 5:
        items.append(_item(
            "Technical Skills", "Medium", "Clarify your technical skills",
            "The skills section contains few recognisable technical skills.",
            f"Recognised in skills section: {', '.join(sorted(in_section)) or 'none'}.",
            "List specific technologies (e.g. 'Python, SQL, Git') rather than general phrases, grouped by category.",
            "Specific tool names are what keyword-based screening looks for.",
        ))
    if len(detected) < 5:
        items.append(_item(
            "Technical Skills", "Medium", "Show more of your technical toolkit",
            "Only a small number of technical skills were identified.",
            f"{len(detected)} skill(s) detected.",
            "If you use additional tools or technologies, name them in your skills section and projects.",
            "A wider set of concrete, relevant skills improves keyword matching.",
        ))
    return items


# ------------------------------------------------------------------ education
def generate_education_feedback(ctx) -> list:
    edu, items = ctx["info"]["education"], []
    if not edu["section_present"]:
        items.append(_item(
            "Education", "High" if not edu["degree_mentioned_elsewhere"] else "Medium",
            "Add a clear education section",
            "No labelled education section was found.",
            "A degree is mentioned elsewhere in the text." if edu["degree_mentioned_elsewhere"]
            else "No degree or institution was detected.",
            "Add an 'Education' section with degree, institution and graduation year.",
            "Education is one of the first things screened for student and graduate roles.",
        ))
        return items
    missing = []
    if not edu["degrees"]:
        missing.append("degree name")
    if not edu["institutions"]:
        missing.append("institution")
    if not edu["years"]:
        missing.append("year/duration")
    if missing:
        items.append(_item(
            "Education", "Medium" if len(missing) > 1 or "degree name" in missing else "Low",
            "Complete your education details",
            "Education information is incomplete.",
            "Not found: " + ", ".join(missing) + ".",
            "Include the full degree name, the institution and the start/graduation year.",
            "Incomplete education entries can fail basic eligibility filters.",
        ))
    return items


# ------------------------------------------------------------------ projects
def generate_projects_feedback(ctx) -> list:
    info, items = ctx["info"], []
    p, exp = info["projects"], info["experience"]
    has_experience = exp["experience_section_present"] or exp["internship_detected"]
    if not p["section_present"]:
        items.append(_item(
            "Technical Projects", "Medium" if has_experience else "High", "Add technical projects",
            "No projects section was detected.",
            "Work experience is present." if has_experience else "No projects or work experience were detected.",
            f"Add 2-3 technical projects relevant to the {ctx['role']['title']} role, each with the problem, "
            "technologies used and your contribution.",
            "Projects are the main evidence of practical skills for students and early-career candidates.",
        ))
        return items
    if p["word_count"] < 40:
        items.append(_item(
            "Technical Projects", "Medium", "Strengthen project descriptions",
            "Project descriptions are brief.",
            f"Projects section contains {p['word_count']} words.",
            "For each project, add 1-3 bullets covering what you built, how, and the outcome.",
            "Brief descriptions make it hard to judge the depth of your work.",
        ))
    if len(ctx["project_skills"]) < 2:
        items.append(_item(
            "Technical Projects", "Medium", "Name the technologies in your projects",
            "Few technologies are mentioned in project descriptions.",
            "Technologies detected in projects: " + (", ".join(sorted(ctx["project_skills"])) or "none") + ".",
            "Mention the languages, libraries and tools used in each project (e.g. 'Built with Python and Pandas').",
            "Technologies inside project descriptions show applied - not just listed - skills.",
        ))
    if len(p["action_verbs"]) < 2:
        items.append(_item(
            "Technical Projects", "Low", "Describe your contributions with action verbs",
            "Your role in each project is not clearly described.",
            "Action verbs found: " + (", ".join(p["action_verbs"]) or "none") + ".",
            "Start bullets with verbs such as 'Developed', 'Implemented', 'Analyzed', 'Deployed'.",
            "Action verbs make your individual contribution explicit.",
        ))
    if p["entry_count"] == 1:
        items.append(_item(
            "Technical Projects", "Low", "Add another project",
            "Only one project was detected.",
            "1 project entry found.",
            "If you have completed other relevant projects (academic, personal or hackathon), add one or two more.",
            "Multiple projects demonstrate breadth and consistency.",
        ))
    return items


# ------------------------------------------------------------------ contact
def generate_contact_feedback(ctx) -> list:
    cand, items = ctx["info"]["candidate"], []
    if not cand["email"]:
        items.append(_item("Contact Information", "High", "Add your email address",
                           "No email address was detected.", "Email pattern not found in the text.",
                           "Add a professional email address at the top of the resume.",
                           "Recruiters cannot contact you without it."))
    if not cand["phone"]:
        items.append(_item("Contact Information", "High", "Add your phone number",
                           "No phone number was detected.", "No 10-13 digit phone number found.",
                           "Add a phone number with country code at the top of the resume.",
                           "Phone is a primary contact channel for interview scheduling."))
    if not cand["name"]:
        items.append(_item("Contact Information", "Medium", "Put your name clearly at the top",
                           "The candidate name could not be identified.",
                           "No name-like line was found in the resume header.",
                           "Place your full name on its own line as the first line of the resume.",
                           "ATS systems create candidate profiles from the name at the top."))
    if not cand["linkedin"]:
        items.append(_item("Contact Information", "Low", "Add a LinkedIn profile link",
                           "No LinkedIn URL was found.", "linkedin.com/in/... not detected.",
                           "If you have a LinkedIn profile, add its URL next to your contact details.",
                           "Recruiters commonly check LinkedIn to verify background and endorsements."))
    if not cand["github"] and not cand["portfolio"]:
        items.append(_item("Contact Information", "Low", "Link your GitHub or portfolio",
                           "No GitHub or portfolio link was found.", "github.com/... or portfolio URL not detected.",
                           "If your code or work is public, link your GitHub profile or portfolio.",
                           "For technical roles, visible work samples strengthen your claims."))
    return items


# ------------------------------------------------------------------ experience / certifications / completeness
def generate_experience_feedback(ctx) -> list:
    info, items = ctx["info"], []
    exp = info["experience"]
    if not exp["internship_detected"] and not exp["experience_section_present"]:
        items.append(_item(
            "Internship Experience", "Medium", "Add internship experience",
            "No internship or work experience was detected.",
            "No Experience/Internship section and no mention of an internship in experience.",
            "If you have completed an internship, industrial training or freelance work, add it with dates and "
            "2-3 bullet points. If not, consider applying for internships to build practical experience.",
            "Practical industry exposure is highly valued for entry-level technical roles.",
        ))
    elif exp["entry_count"] and exp["date_ranges"] == 0:
        items.append(_item(
            "Internship Experience", "Low", "Add dates to your experience",
            "Experience entries have no detectable date ranges.",
            f"{exp['entry_count']} experience entr(ies), 0 date ranges.",
            "Add start and end dates (e.g. 'Jun 2024 - Aug 2024') to each role.",
            "Dates let recruiters and ATS calculate the length of experience.",
        ))
    return items


def generate_certification_feedback(ctx) -> list:
    info = ctx["info"]
    if info["certifications"] or info["certification_mentioned"]:
        return []
    suggestions = ctx["role"].get("certifications", [])
    coverage = ctx["role_match"]["match_percentage"]
    return [_item(
        "Certifications", "Medium" if coverage < 50 else "Low", "Include certifications",
        "No certifications section was detected.",
        "No 'Certifications' heading or certificate mention found.",
        "If you hold relevant certifications or completed courses, list them with the issuer and year."
        + (f" Examples relevant to {ctx['role']['title']}: " + "; ".join(suggestions[:3]) + "." if suggestions else ""),
        "Certifications are optional, but they can validate skills - especially where keyword coverage is low.",
    )]


def generate_completeness_feedback(ctx) -> list:
    info, items = ctx["info"], []
    if "summary" not in info["sections"]:
        items.append(_item(
            "Resume Completeness", "Medium", "Add a professional summary",
            "No summary or objective was found.", "No Summary/Objective/Profile heading detected.",
            f"Add a 2-3 line summary stating your background and your goal of working as a {ctx['role']['title']}.",
            "A summary frames the rest of the resume and is a natural place for role keywords.",
        ))
    if len(info["metrics"]) < 2:
        items.append(_item(
            "Resume Completeness", "Medium", "Add measurable outcomes",
            "Few quantified results were found.",
            "Quantified results detected: " + (", ".join(info["metrics"]) or "none") + ".",
            "Where accurate, quantify impact (e.g. 'reduced processing time by 30%', 'dataset of 10,000 rows').",
            "Numbers make achievements concrete and comparable.",
        ))
    empty = [SECTION_LABELS.get(k, k) for k, v in info["sections"].items()
             if v["word_count"] < 5 and k not in ("other", "activities")]
    if empty:
        items.append(_item(
            "Resume Completeness", "Low", "Fill in empty sections",
            "Some sections have a heading but little or no content.",
            "Sections: " + ", ".join(empty) + ".",
            "Add content to these sections or remove the empty headings.",
            "Empty sections look unfinished and waste space.",
        ))
    return items


# ------------------------------------------------------------------ ATS / role
def generate_ats_feedback(ctx) -> list:
    role, match, items = ctx["role"], ctx["role_match"], []
    missing = match["missing"]
    tips = role.get("keyword_tips", {})
    used_titles = set()

    for kw in missing:
        if kw in tips and tips[kw]["title"] not in used_titles:
            used_titles.add(tips[kw]["title"])
            items.append(_item(
                "ATS Keywords", "High" if kw in match["core_missing"] else "Medium", tips[kw]["title"],
                f"'{kw}' was not detected in your resume.",
                f"'{kw}' is one of {len(match['reference_keywords'])} reference keywords for {role['title']}; "
                f"{len(match['matched'])} were matched.",
                tips[kw]["text"],
                f"{kw} is a relevant keyword for the selected {role['title']} role. A missing keyword does not "
                "mean you lack the skill - only that it is not visible to keyword-based screening.",
            ))

    for group in role.get("group_tips", []):
        if not any(k in ctx["detected_skills"] for k in group["any_of"]) and group["title"] not in used_titles:
            used_titles.add(group["title"])
            items.append(_item(
                "ATS Keywords", "High", group["title"],
                "None of these were detected: " + ", ".join(group["any_of"]) + ".",
                f"Role keyword coverage is {match['match_percentage']}%.",
                group["text"],
                f"These technologies are central to most {role['title']} job descriptions.",
            ))

    for tip in role.get("project_tips", []):
        skill = tip["skill"]
        if skill in ctx["detected_skills"] and skill not in ctx["project_skills"] and ctx["info"]["projects"]["section_present"]:
            items.append(_item(
                "Technical Projects", "Medium", tip["title"],
                f"{skill} is listed but does not appear in any project description.",
                f"{skill} detected elsewhere in the resume; not found in the Projects section.",
                tip["text"],
                "Demonstrating a skill inside a project is more convincing than listing it.",
            ))

    remaining = [k for k in missing if k not in tips]
    if remaining:
        cov = match["match_percentage"]
        items.append(_item(
            "ATS Keywords", "High" if cov < 40 else "Medium" if cov < 70 else "Low",
            "Cover more role-relevant keywords",
            f"{len(missing)} of {len(match['reference_keywords'])} {role['title']} reference keywords are missing.",
            "Missing: " + ", ".join(remaining) + ".",
            "For each keyword you genuinely have experience with, mention it in your skills and show it in a "
            "project or experience bullet. Do not add skills you do not have.",
            "Keyword-based screening compares your resume against role terms; the dictionary is an editable "
            "reference, not a definitive requirement list.",
        ))

    summary = (ctx["info"].get("summary") or "").lower()
    if summary and not any(re.search(rf"\b{re.escape(t)}\b", summary) for t in role.get("summary_terms", [])):
        items.append(_item(
            "Role Alignment", "Low", f"Align your summary with the {role['title']} role",
            "Your summary does not mention the target role or its domain.",
            "Summary text did not contain: " + ", ".join(role.get("summary_terms", [])[:5]) + ".",
            f"Mention your interest in {role['title']} work and your most relevant skills in the summary.",
            "A role-aligned summary signals fit immediately and adds relevant keywords.",
        ))
    return items


# ------------------------------------------------------------------ final
def generate_final_recommendations(ctx) -> list:
    generators = (
        generate_contact_feedback, generate_structure_feedback, generate_skills_feedback,
        generate_ats_feedback, generate_projects_feedback, generate_education_feedback,
        generate_experience_feedback, generate_completeness_feedback, generate_certification_feedback,
    )
    seen, results = set(), []
    for gen in generators:
        for item in gen(ctx):
            key = item["title"].lower()
            if key in seen:
                continue
            seen.add(key)
            results.append(item)
    # Stable sort keeps generator order within a priority level.
    results.sort(key=lambda i: PRIORITY_ORDER[i["priority"]])
    return results
