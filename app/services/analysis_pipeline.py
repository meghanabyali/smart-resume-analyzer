"""Orchestrates the 7-step project workflow.

Step 1-3 (upload, extract, process)  -> ``process_upload``
Step 4-6 (score, ATS, suggestions)   -> ``run_analysis``
Step 7 (dashboard) is rendered from the stored Analysis record.
"""
import json
import logging

from flask import current_app

from ..models import Analysis, Feedback, Resume, db
from . import ResumeProcessingError
from .ats_analyzer import calculate_ats_score
from .feedback_engine import generate_final_recommendations
from .file_handler import delete_stored_file, safe_display_name, store_file, validate_upload
from .resume_parser import extract_document
from .resume_scorer import calculate_total_resume_score
from .section_extractor import extract_resume_information
from .skill_matcher import detect_skills, group_by_category, load_roles, load_skill_dictionary, match_role_skills
from .text_preprocessor import extract_noun_phrases, extract_top_keywords, nlp_backend_name

log = logging.getLogger(__name__)


def get_roles() -> dict:
    return load_roles(current_app.config["JOB_ROLES_FILE"])


def get_skill_dictionary() -> dict:
    return load_skill_dictionary(current_app.config["SKILL_KEYWORDS_FILE"])


# ------------------------------------------------------------------ steps 1-3
def process_upload(filename: str, content: bytes) -> Resume:
    cfg = current_app.config
    max_bytes = int(cfg["MAX_UPLOAD_MB"] * 1024 * 1024)
    file_type = validate_upload(filename, content, cfg["ALLOWED_EXTENSIONS"], max_bytes)

    document = extract_document(content, file_type)  # raises ResumeProcessingError on failure
    info = extract_resume_information(document["text"], document.get("headings", []))
    detected = detect_skills(info["clean_text"], get_skill_dictionary())

    stored_name = store_file(content, file_type, cfg["UPLOAD_FOLDER"]) if cfg["KEEP_UPLOADED_FILES"] else ""

    extracted = {
        "document": {
            "page_count": document["page_count"],
            "word_count": document["word_count"],
            "metadata": document["metadata"],
            "layout": document["layout"],
            "file_type": file_type,
        },
        **{k: v for k, v in info.items() if k != "clean_text"},
        "technical_skills": detected,
        "skills_by_category": group_by_category(detected),
    }
    resume = Resume(
        original_filename=safe_display_name(filename),
        stored_filename=stored_name,
        file_type=file_type,
        file_size=len(content),
        extracted_text=info["clean_text"],
        extracted_data_json=json.dumps(extracted),
    )
    try:
        db.session.add(resume)
        db.session.commit()
    except Exception:
        db.session.rollback()
        delete_stored_file(stored_name, cfg["UPLOAD_FOLDER"])
        raise
    # Log metadata only - never resume contents.
    log.info("Stored resume %s (%s, %d words)", resume.id, file_type, document["word_count"])
    return resume


# ------------------------------------------------------------------ steps 4-6
def build_analysis(resume: Resume, role_id: str) -> dict:
    """Pure analysis (no database writes) - also used directly by tests."""
    roles = get_roles()
    if role_id not in roles:
        raise ResumeProcessingError(
            f"Invalid job role '{role_id}'. Choose one of: {', '.join(roles)}.", 400
        )
    role = {"id": role_id, **roles[role_id]}
    dictionary = get_skill_dictionary()
    data = resume.extracted_data
    info = {**data, "clean_text": resume.extracted_text}
    document = {**data["document"]}

    detected = detect_skills(resume.extracted_text, dictionary)
    sections = info["sections"]
    skills_in_section = detect_skills(sections.get("skills", {}).get("content", ""), dictionary)
    project_skills = detect_skills(sections.get("projects", {}).get("content", ""), dictionary)
    role_match = match_role_skills(detected, role)

    cfg = current_app.config
    resume_score = calculate_total_resume_score(
        info, document, detected, skills_in_section, project_skills, role_match,
        cfg.get("RESUME_SCORE_WEIGHTS"), cfg.get("SCORE_CATEGORIES"),
    )
    ats = calculate_ats_score(document, info, role_match, cfg.get("ATS_WEIGHTS"))

    ctx = {
        "info": info, "document": document, "role": role, "role_match": role_match,
        "detected_skills": detected, "skills_in_section": skills_in_section,
        "project_skills": project_skills, "resume_score": resume_score, "ats": ats,
    }
    feedback = generate_final_recommendations(ctx)

    return {
        "role": {"id": role_id, "title": role["title"], "description": role["description"]},
        "resume_score": resume_score,
        "score_category": resume_score["category"],
        "ats": ats,
        "skills": {
            **role_match,
            "detected": sorted(detected),
            "detected_by_category": group_by_category(detected),
            "in_skills_section": sorted(skills_in_section),
            "in_projects": sorted(project_skills),
        },
        "candidate": info["candidate"],
        "sections_detected": info["section_order"],
        "document": document,
        "nlp": {
            "backend": nlp_backend_name(),
            "top_keywords": extract_top_keywords(resume.extracted_text),
            "noun_phrases": extract_noun_phrases(resume.extracted_text),
        },
        "feedback": feedback,
    }


def run_analysis(resume: Resume, role_id: str) -> Analysis:
    result = build_analysis(resume, role_id)
    params = {p["key"]: p["score"] for p in result["resume_score"]["parameters"]}
    feedback = result.pop("feedback")

    analysis = Analysis(
        resume_id=resume.id,
        target_role=role_id,
        resume_score=result["resume_score"]["total"],
        ats_score=result["ats"]["score"],
        keyword_match_percentage=result["skills"]["match_percentage"],
        structure_score=params["structure"],
        skills_score=params["skills"],
        education_score=params["education"],
        projects_score=params["projects"],
        contact_score=params["contact"],
        completeness_score=params["completeness"],
        analysis_details_json=json.dumps(result),
    )
    for pos, item in enumerate(feedback):
        analysis.feedback_items.append(Feedback(position=pos, **item))
    try:
        db.session.add(analysis)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    log.info("Analysis %s created for resume %s (role=%s)", analysis.id, resume.id, role_id)
    return analysis


def delete_resume(resume: Resume) -> None:
    stored = resume.stored_filename
    db.session.delete(resume)  # cascades to analyses and feedback
    db.session.commit()
    delete_stored_file(stored, current_app.config["UPLOAD_FOLDER"])
