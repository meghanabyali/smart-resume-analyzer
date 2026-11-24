"""Application configuration.

All secrets and deployment-specific values come from environment variables
(see .env.example). Defaults are safe for local development only.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        instance_dir = BASE_DIR / "instance"
        instance_dir.mkdir(exist_ok=True)
        return f"sqlite:///{(instance_dir / 'resume_analyzer.db').as_posix()}"
    # Some hosts still hand out the legacy "postgres://" scheme.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Upload handling -------------------------------------------------
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_UPLOAD_MB = float(os.environ.get("MAX_UPLOAD_MB", "5"))
    # Flask rejects request bodies above this size with HTTP 413.
    # A small allowance is added for multipart form overhead.
    MAX_CONTENT_LENGTH = int(MAX_UPLOAD_MB * 1024 * 1024) + 64 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    KEEP_UPLOADED_FILES = _bool("KEEP_UPLOADED_FILES", True)

    # ---- Privacy -----------------------------------------------------------
    # Resumes and analyses older than this are purged automatically.
    # 0 disables automatic purging.
    RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "7"))

    # ---- Reference data ----------------------------------------------------
    JOB_ROLES_FILE = str(DATA_DIR / "job_roles.json")
    SKILL_KEYWORDS_FILE = str(DATA_DIR / "skill_keywords.json")

    # ---- Scoring configuration (application-defined, not ATS standards) ----
    RESUME_SCORE_WEIGHTS = {
        "structure": 20,
        "skills": 20,
        "education": 15,
        "projects": 15,
        "contact": 15,
        "completeness": 15,
    }
    ATS_WEIGHTS = {"keyword_coverage": 0.60, "parseability": 0.20, "structure": 0.20}
    SCORE_CATEGORIES = [
        (85, "Excellent"),
        (70, "Good"),
        (50, "Needs Improvement"),
        (0, "Significant Improvement Needed"),
    ]

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    RETENTION_DAYS = 0


class ProductionConfig(Config):
    DEBUG = False
