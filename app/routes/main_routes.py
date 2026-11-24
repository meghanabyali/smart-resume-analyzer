"""Page routes: home, upload, dashboard, printable report, about, health."""
from flask import Blueprint, current_app, jsonify, render_template
from sqlalchemy import text

from ..models import db
from ..services.analysis_pipeline import get_roles
from ..services.text_preprocessor import nlp_backend_name
from . import get_analysis_or_404

main_bp = Blueprint("main", __name__)


@main_bp.app_context_processor
def inject_globals():
    return {"retention_days": current_app.config["RETENTION_DAYS"],
            "max_upload_mb": current_app.config["MAX_UPLOAD_MB"]}


@main_bp.get("/")
def index():
    return render_template("index.html", roles=get_roles())


@main_bp.get("/upload")
def upload_page():
    return render_template("upload.html", roles=get_roles())


@main_bp.get("/dashboard/<token>")
def dashboard(token):
    analysis = get_analysis_or_404(token)
    return render_template("dashboard.html", a=analysis.to_dict())


@main_bp.get("/report/<token>")
def report(token):
    analysis = get_analysis_or_404(token)
    return render_template("report.html", a=analysis.to_dict())


@main_bp.get("/about")
def about():
    return render_template("about.html", roles=get_roles())


@main_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return jsonify({"status": "ok" if db_ok else "degraded", "database": db_ok,
                    "nlp_backend": nlp_backend_name()}), status
