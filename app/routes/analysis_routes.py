"""Modules 2-4 API: run analysis, fetch results, list roles."""
import logging

from flask import Blueprint, request, url_for

from ..models import Resume
from ..services import ResumeProcessingError
from ..services.analysis_pipeline import delete_resume, get_roles, run_analysis
from . import get_analysis_or_404, json_error, json_ok

log = logging.getLogger(__name__)
analysis_bp = Blueprint("analysis", __name__, url_prefix="/api")


@analysis_bp.get("/roles")
def list_roles():
    roles = get_roles()
    return json_ok({"roles": [
        {"id": rid, "title": r["title"], "description": r["description"], "keywords": r["keywords"]}
        for rid, r in roles.items()
    ]})


@analysis_bp.post("/analyze")
def analyze():
    payload = request.get_json(silent=True) or request.form
    resume_token = (payload.get("resume_id") or "").strip()
    role_id = (payload.get("role") or "").strip()
    if not resume_token:
        return json_error("'resume_id' is required.", 400)
    if not role_id:
        return json_error("'role' is required.", 400)
    if role_id not in get_roles():
        return json_error(f"Invalid job role '{role_id}'.", 400)

    resume = Resume.query.filter_by(public_id=resume_token).first()
    if resume is None:
        return json_error("Resume not found. It may have been deleted or expired.", 404)
    try:
        analysis = run_analysis(resume, role_id)
    except ResumeProcessingError as exc:
        return json_error(exc.message, exc.status_code)
    except Exception:
        log.exception("Unexpected error during analysis")
        return json_error("The analysis failed due to an unexpected error.", 500)

    return json_ok({
        "analysis_id": analysis.public_id,
        "resume_score": analysis.resume_score,
        "ats_score": analysis.ats_score,
        "dashboard_url": url_for("main.dashboard", token=analysis.public_id),
    }, 201)


@analysis_bp.get("/analysis/<token>")
def get_analysis(token):
    return json_ok({"analysis": get_analysis_or_404(token).to_dict()})


@analysis_bp.delete("/analysis/<token>")
def delete_analysis(token):
    """Delete an analysis together with its resume (removes all personal data)."""
    analysis = get_analysis_or_404(token)
    delete_resume(analysis.resume)
    return json_ok({"message": "Analysis, resume and stored file were permanently deleted."})
