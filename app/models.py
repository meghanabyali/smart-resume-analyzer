"""Database models: Resume -> Analysis -> Feedback.

Records are exposed to the outside world only through random, unguessable
tokens (``public_id``) because the prototype has no user accounts.
"""
import json
import secrets
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _token() -> str:
    return secrets.token_urlsafe(18)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, nullable=False, index=True, default=_token)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    extracted_data_json = db.Column(db.Text, nullable=False, default="{}")
    uploaded_at = db.Column(db.DateTime, nullable=False, default=_now, index=True)

    analyses = db.relationship(
        "Analysis", backref="resume", cascade="all, delete-orphan", lazy=True
    )

    @property
    def extracted_data(self) -> dict:
        return json.loads(self.extracted_data_json or "{}")

    def to_dict(self) -> dict:
        data = self.extracted_data
        return {
            "id": self.public_id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "uploaded_at": self.uploaded_at.isoformat() + "Z",
            "page_count": data.get("document", {}).get("page_count"),
            "word_count": data.get("document", {}).get("word_count"),
            "candidate": data.get("candidate", {}),
            "sections_detected": data.get("section_order", []),
        }


class Analysis(db.Model):
    __tablename__ = "analyses"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, nullable=False, index=True, default=_token)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=False, index=True)
    target_role = db.Column(db.String(50), nullable=False)
    resume_score = db.Column(db.Integer, nullable=False)
    ats_score = db.Column(db.Integer, nullable=False)
    keyword_match_percentage = db.Column(db.Float, nullable=False)
    structure_score = db.Column(db.Float, nullable=False)
    skills_score = db.Column(db.Float, nullable=False)
    education_score = db.Column(db.Float, nullable=False)
    projects_score = db.Column(db.Float, nullable=False)
    contact_score = db.Column(db.Float, nullable=False)
    completeness_score = db.Column(db.Float, nullable=False)
    analysis_details_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, nullable=False, default=_now, index=True)

    feedback_items = db.relationship(
        "Feedback", backref="analysis", cascade="all, delete-orphan", lazy=True,
        order_by="Feedback.position",
    )

    @property
    def details(self) -> dict:
        return json.loads(self.analysis_details_json or "{}")

    def to_dict(self) -> dict:
        details = self.details
        return {
            "id": self.public_id,
            "resume_id": self.resume.public_id,
            "original_filename": self.resume.original_filename,
            "target_role": self.target_role,
            "target_role_title": details.get("role", {}).get("title", self.target_role),
            "created_at": self.created_at.isoformat() + "Z",
            "resume_score": self.resume_score,
            "score_category": details.get("score_category"),
            "ats_score": self.ats_score,
            "keyword_match_percentage": self.keyword_match_percentage,
            "parameter_scores": {
                "structure": self.structure_score,
                "skills": self.skills_score,
                "education": self.education_score,
                "projects": self.projects_score,
                "contact": self.contact_score,
                "completeness": self.completeness_score,
            },
            "details": details,
            "feedback": [f.to_dict() for f in self.feedback_items],
        }


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    issue = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.Text, nullable=False, default="")
    recommendation = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "issue": self.issue,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
        }
