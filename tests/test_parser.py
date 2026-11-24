"""Module 1 - validation, extraction and information-extraction tests."""
import pytest

from app.services import ResumeProcessingError
from app.services.file_handler import validate_upload
from app.services.resume_parser import extract_document
from app.services.section_extractor import extract_contact, extract_resume_information, match_heading
from app.services.text_preprocessor import clean_text, extract_top_keywords, tokenize
from conftest import STRONG_RESUME, make_docx, make_image_only_pdf, make_pdf

MAX = 5 * 1024 * 1024
ALLOWED = {"pdf", "docx"}


# ---------------------------------------------------------------- validation
def test_rejects_unsupported_extension():
    with pytest.raises(ResumeProcessingError) as e:
        validate_upload("resume.txt", b"hello", ALLOWED, MAX)
    assert e.value.status_code == 415


def test_rejects_renamed_file_with_wrong_content():
    with pytest.raises(ResumeProcessingError):
        validate_upload("resume.pdf", b"MZ\x90\x00 not a pdf", ALLOWED, MAX)
    with pytest.raises(ResumeProcessingError):
        validate_upload("resume.docx", b"%PDF-1.4 fake", ALLOWED, MAX)


def test_rejects_empty_and_oversized():
    with pytest.raises(ResumeProcessingError):
        validate_upload("resume.pdf", b"", ALLOWED, MAX)
    with pytest.raises(ResumeProcessingError) as e:
        validate_upload("resume.pdf", b"%PDF-" + b"0" * 100, ALLOWED, 50)
    assert e.value.status_code == 413


def test_accepts_valid_pdf_and_docx():
    assert validate_upload("cv.PDF", make_pdf(STRONG_RESUME), ALLOWED, MAX) == "pdf"
    assert validate_upload("cv.docx", make_docx(STRONG_RESUME), ALLOWED, MAX) == "docx"


# ---------------------------------------------------------------- extraction
def test_pdf_text_extraction():
    doc = extract_document(make_pdf(STRONG_RESUME), "pdf")
    assert "Priya Nair" in doc["text"]
    assert doc["page_count"] == 1
    assert doc["word_count"] > 100


def test_docx_text_extraction_includes_headings_and_lists():
    doc = extract_document(make_docx(STRONG_RESUME), "docx")
    assert "Technical Skills" in doc["headings"]
    assert "• Built a Power BI dashboard" in doc["text"]


def test_corrupted_pdf_is_rejected():
    with pytest.raises(ResumeProcessingError):
        extract_document(b"%PDF-1.7\n garbage garbage", "pdf")


def test_image_only_pdf_reports_ocr_not_supported():
    with pytest.raises(ResumeProcessingError) as e:
        extract_document(make_image_only_pdf(), "pdf")
    assert "scanned" in e.value.message.lower()


def test_empty_docx_is_rejected():
    with pytest.raises(ResumeProcessingError):
        extract_document(make_docx(""), "docx")


# ---------------------------------------------------------------- NLP / info extraction
def test_clean_text_normalises_bullets_and_ligatures():
    out = clean_text("●  Built ﬁve apps\n\n\n\n▪ Led team")
    assert out == "• Built five apps\n\n• Led team"


def test_tokenizer_preserves_technical_terms():
    tokens = tokenize("Skilled in C++, C#, Node.js and CI/CD")
    assert {"C++", "C#", "Node.js", "CI/CD"} <= set(tokens)


def test_heading_detection():
    assert match_heading("TECHNICAL SKILLS")[0] == "skills"
    assert match_heading("Work Experience:")[0] == "experience"
    assert match_heading("Skills: Python, SQL") == ("skills", "Python, SQL")
    assert match_heading("Developed a dashboard using Python and SQL for sales")[0] is None


def test_contact_extraction():
    c = extract_contact("a.b@example.com | +91 98765 43210 | linkedin.com/in/ab | github.com/ab | 2019 - 2023")
    assert c["email"] == "a.b@example.com"
    assert c["phone"] == "+91 98765 43210"
    assert c["linkedin"] and c["github"]


def test_date_range_is_not_a_phone():
    assert extract_contact("B.Tech 2019 - 2023")["phone"] is None


def test_full_information_extraction():
    info = extract_resume_information(STRONG_RESUME)
    assert info["candidate"]["name"] == "Priya Nair"
    assert {"summary", "education", "skills", "projects", "internships", "certifications"} <= set(info["section_order"])
    assert info["education"]["degrees"] and info["education"]["institutions"]
    assert info["experience"]["internship_detected"]
    assert info["metrics"]


def test_missing_fields_are_not_invented():
    info = extract_resume_information("Some text without any contact details at all here\nSKILLS\nPython")
    assert info["candidate"]["email"] is None
    assert info["candidate"]["phone"] is None


def test_top_keywords_are_extracted():
    terms = [k["term"] for k in extract_top_keywords(STRONG_RESUME)]
    assert terms and "the" not in terms
