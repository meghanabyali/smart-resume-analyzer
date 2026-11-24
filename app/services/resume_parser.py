"""Module 1 - text extraction from PDF (PyMuPDF) and DOCX (python-docx)."""
import io
import logging

import fitz  # PyMuPDF
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from . import ResumeProcessingError

log = logging.getLogger(__name__)

MIN_WORDS = 15  # below this the document cannot be meaningfully analysed


def extract_document(content: bytes, file_type: str) -> dict:
    """Return {'text', 'page_count', 'metadata', 'layout', 'headings'}."""
    if file_type == "pdf":
        result = extract_pdf(content)
    elif file_type == "docx":
        result = extract_docx(content)
    else:
        raise ResumeProcessingError("Unsupported file type.", 415)

    words = len(result["text"].split())
    result["word_count"] = words
    if words == 0:
        raise ResumeProcessingError(
            "No text could be extracted from this document. If it is a scanned image, "
            "please upload a text-based PDF or DOCX - OCR is not supported in this prototype.", 422
        )
    if words < MIN_WORDS:
        raise ResumeProcessingError(
            f"Only {words} words could be extracted, which is too little to analyse reliably. "
            "Please upload a complete, text-based resume.", 422
        )
    return result


# --------------------------------------------------------------------------- PDF
def extract_pdf(content: bytes) -> dict:
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception:  # PyMuPDF raises several types for broken files
        raise ResumeProcessingError("The PDF appears to be corrupted and could not be opened.", 422)

    try:
        if doc.needs_pass or doc.is_encrypted:
            raise ResumeProcessingError(
                "This PDF is password-protected. Please remove the password and upload it again.", 422
            )
        if doc.page_count == 0:
            raise ResumeProcessingError("The PDF has no pages.", 422)

        page_texts, image_count = [], 0
        left_words = right_words = 0
        for page in doc:
            page_texts.append(page.get_text("text", sort=True))
            image_count += len(page.get_images(full=False))
            width = page.rect.width or 1
            for block in page.get_text("blocks"):
                x0, _y0, x1, _y1, text, *_ = block
                n = len(text.split())
                if x1 < width * 0.55:
                    left_words += n
                elif x0 > width * 0.45:
                    right_words += n

        text = "\n".join(page_texts)
        if len(text.split()) == 0 and image_count:
            raise ResumeProcessingError(
                "This PDF appears to be a scanned image with no selectable text. Text extraction "
                "(OCR) for scanned resumes is not available in this prototype - please upload a "
                "text-based PDF or a DOCX file.", 422
            )
        # Substantial text on both halves of the page suggests a multi-column layout,
        # which some ATS parsers read out of order.
        multi_column = left_words >= 40 and right_words >= 40

        meta = {k: v for k, v in (doc.metadata or {}).items() if v and k in {"title", "author", "creator", "producer"}}
        return {
            "text": text,
            "page_count": doc.page_count,
            "metadata": meta,
            "headings": [],
            "layout": {
                "multi_column": multi_column,
                "image_count": image_count,
                "table_count": 0,
            },
        }
    finally:
        doc.close()


# -------------------------------------------------------------------------- DOCX
def _iter_block_items(document):
    """Yield paragraphs and tables in the order they appear in the body."""
    body = document.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            yield Paragraph(child, document)
        elif tag == "tbl":
            yield Table(child, document)


def _paragraph_line(par: Paragraph) -> str:
    text = par.text.strip()
    if not text:
        return ""
    style = (par.style.name if par.style is not None else "") or ""
    is_list = "List" in style or par._p.pPr is not None and par._p.pPr.numPr is not None
    return f"• {text}" if is_list and not text.startswith(("•", "-", "*")) else text


def extract_docx(content: bytes) -> dict:
    try:
        document = Document(io.BytesIO(content))
    except Exception:
        raise ResumeProcessingError("The DOCX file appears to be corrupted and could not be opened.", 422)

    lines, headings, table_count = [], [], 0

    # Contact details are often placed in the page header.
    for section in document.sections:
        try:
            for par in section.header.paragraphs:
                if par.text.strip():
                    lines.append(par.text.strip())
        except Exception:  # headers are optional; ignore malformed ones
            pass

    for block in _iter_block_items(document):
        if isinstance(block, Paragraph):
            line = _paragraph_line(block)
            if not line:
                continue
            style = (block.style.name if block.style is not None else "") or ""
            if style.startswith("Heading") or style == "Title":
                headings.append(line)
            lines.append(line)
        else:
            table_count += 1
            for row in block.rows:
                seen, cells = set(), []
                for cell in row.cells:  # merged cells repeat; de-duplicate
                    t = cell.text.strip()
                    if t and t not in seen:
                        seen.add(t)
                        cells.append(t)
                if cells:
                    lines.extend(cells if len(" ".join(cells)) > 80 else [" | ".join(cells)])

    props = document.core_properties
    meta = {k: v for k, v in {"title": props.title, "author": props.author}.items() if v}
    text = "\n".join(lines)
    # DOCX has no fixed pages; estimate roughly 500 words per page.
    page_estimate = max(1, round(len(text.split()) / 500 + 0.49))
    return {
        "text": text,
        "page_count": page_estimate,
        "metadata": meta,
        "headings": headings,
        "layout": {
            "multi_column": False,
            "image_count": len(document.inline_shapes),
            "table_count": table_count,
        },
    }
