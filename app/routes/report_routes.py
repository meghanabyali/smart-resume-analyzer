"""Module 5 API: downloadable PDF report."""
import re

from flask import Blueprint, Response

from ..services.report_generator import generate_pdf_report
from . import get_analysis_or_404

report_bp = Blueprint("report", __name__, url_prefix="/api/reports")


@report_bp.get("/<token>/pdf")
def download_pdf(token):
    analysis = get_analysis_or_404(token).to_dict()
    pdf = generate_pdf_report(analysis)
    base = re.sub(r"[^A-Za-z0-9_\-]", "_", analysis["original_filename"].rsplit(".", 1)[0])[:50] or "resume"
    filename = f"resume_analysis_{base}_{analysis['target_role']}.pdf"
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"',
                             "Cache-Control": "no-store"})
