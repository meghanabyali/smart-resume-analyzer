"""Module 1 API: upload / parse / delete resumes."""
import logging

from flask import Blueprint, request

from ..services import ResumeProcessingError
from ..services.analysis_pipeline import delete_resume, process_upload
from ..services.retention import purge_expired
from . import get_resume_or_404, json_error, json_ok

log = logging.getLogger(__name__)
upload_bp = Blueprint("upload", __name__, url_prefix="/api")


@upload_bp.post("/resumes/upload")
def upload_resume():
    file = request.files.get("resume")
    if file is None or not file.filename:
        return json_error("No file was uploaded. Attach a PDF or DOCX file in the 'resume' field.", 400)
    try:
        purge_expired()
        content = file.read()
        resume = process_upload(file.filename, content)
    except ResumeProcessingError as exc:
        return json_error(exc.message, exc.status_code)
    except Exception:
        log.exception("Unexpected error while processing an upload")
        return json_error("The resume could not be processed due to an unexpected error.", 500)
    return json_ok({"resume": resume.to_dict()}, 201)


@upload_bp.get("/resumes/<token>")
def get_resume(token):
    resume = get_resume_or_404(token)
    return json_ok({"resume": resume.to_dict(),
                    "analyses": [a.public_id for a in resume.analyses]})


@upload_bp.delete("/resumes/<token>")
def remove_resume(token):
    resume = get_resume_or_404(token)
    delete_resume(resume)
    return json_ok({"message": "Resume and all related analyses were permanently deleted."})
