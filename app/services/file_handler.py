"""Module 1 - upload validation and safe storage."""
import io
import os
import uuid
import zipfile

from werkzeug.utils import secure_filename

from . import ResumeProcessingError

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_upload(filename: str, content: bytes, allowed_extensions, max_bytes: int) -> str:
    """Validate the name, size and *content* of an upload. Returns the file type."""
    if not filename:
        raise ResumeProcessingError("No file was selected. Please choose a PDF or DOCX resume.")

    ext = get_extension(filename)
    if ext not in allowed_extensions:
        raise ResumeProcessingError(
            f"Unsupported file type '.{ext or '?'}'. Only PDF and DOCX resumes are accepted.", 415
        )

    if not content:
        raise ResumeProcessingError("The uploaded file is empty.")
    if len(content) > max_bytes:
        raise ResumeProcessingError(
            f"The file is too large. The maximum allowed size is {max_bytes / (1024 * 1024):g} MB.", 413
        )

    # Check the real content, not just the extension (a renamed .exe is rejected here).
    if ext == "pdf" and not content[:1024].lstrip().startswith(PDF_MAGIC):
        raise ResumeProcessingError("The file has a .pdf extension but is not a valid PDF document.", 415)
    if ext == "docx":
        if not content.startswith(ZIP_MAGIC):
            raise ResumeProcessingError("The file has a .docx extension but is not a valid Word document.", 415)
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise ResumeProcessingError("The DOCX file is missing its document body.", 415)
        except zipfile.BadZipFile:
            raise ResumeProcessingError("The DOCX file appears to be corrupted.", 415)
    return ext


def safe_display_name(filename: str) -> str:
    """Sanitised original filename for display/storage (never used as a path)."""
    cleaned = secure_filename(filename) or "resume"
    return cleaned[:200]


def store_file(content: bytes, ext: str, upload_folder: str) -> str:
    """Write the upload under a random name and return that name.

    The user-supplied filename is never used to build the path, which rules
    out path traversal.
    """
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.abspath(upload_folder)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, stored_name)
    with open(path, "wb") as fh:
        fh.write(content)
    return stored_name


def delete_stored_file(stored_name: str, upload_folder: str) -> None:
    if not stored_name:
        return
    folder = os.path.abspath(upload_folder)
    path = os.path.abspath(os.path.join(folder, os.path.basename(stored_name)))
    if path.startswith(folder) and os.path.isfile(path):
        os.remove(path)
