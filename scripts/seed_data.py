"""Initialise the database and (optionally) load the synthetic sample resumes.

Usage:
    python scripts/seed_data.py            # create tables only
    python scripts/seed_data.py --samples  # also upload + analyse every sample resume

Prints the dashboard URL of each analysed sample - handy for demos.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app import create_app  # noqa: E402
from app.models import db  # noqa: E402
from app.services import ResumeProcessingError  # noqa: E402
from app.services.analysis_pipeline import process_upload, run_analysis  # noqa: E402

ROLE_PREFIXES = ("data_analyst", "web_developer", "ai_engineer", "cloud_engineer")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", action="store_true", help="analyse data/sample_resumes/*")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()
        print(f"Database ready: {app.config['SQLALCHEMY_DATABASE_URI']}")
        if not args.samples:
            return 0
        sample_dir = ROOT / "data" / "sample_resumes"
        for path in sorted(sample_dir.glob("*.*")):
            if path.suffix.lower() not in {".pdf", ".docx"}:
                continue
            role = next((r for r in ROLE_PREFIXES if path.name.startswith(r)), "data_analyst")
            try:
                resume = process_upload(path.name, path.read_bytes())
                analysis = run_analysis(resume, role)
            except ResumeProcessingError as exc:
                print(f"  {path.name}: skipped - {exc.message}")
                continue
            print(f"  {path.name:40s} {role:15s} resume={analysis.resume_score:3d} ats={analysis.ats_score:3d}"
                  f"  /dashboard/{analysis.public_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
