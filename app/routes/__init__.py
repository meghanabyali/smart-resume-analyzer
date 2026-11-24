"""HTTP routes (thin controllers that delegate to app.services)."""
from flask import abort, jsonify

from ..models import Analysis, Resume


def json_ok(payload: dict, status: int = 200):
    return jsonify({"success": True, **payload}), status


def json_error(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


def get_analysis_or_404(token: str) -> Analysis:
    analysis = Analysis.query.filter_by(public_id=token).first()
    if analysis is None:
        abort(404)
    return analysis


def get_resume_or_404(token: str) -> Resume:
    resume = Resume.query.filter_by(public_id=token).first()
    if resume is None:
        abort(404)
    return resume
