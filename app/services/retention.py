"""Privacy: automatic purge of resumes older than ``RETENTION_DAYS``."""
import logging
from datetime import datetime, timedelta, timezone

from flask import current_app

from ..models import Resume, db
from .file_handler import delete_stored_file

log = logging.getLogger(__name__)


def purge_expired() -> int:
    days = current_app.config.get("RETENTION_DAYS", 0)
    if not days or days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    expired = Resume.query.filter(Resume.uploaded_at < cutoff).all()
    for resume in expired:
        delete_stored_file(resume.stored_filename, current_app.config["UPLOAD_FOLDER"])
        db.session.delete(resume)
    if expired:
        db.session.commit()
        log.info("Purged %d expired resume(s) older than %d days", len(expired), days)
    return len(expired)
