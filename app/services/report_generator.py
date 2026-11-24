"""Module 5 - downloadable PDF analysis report (ReportLab), built from stored analysis data."""
import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#14213d")
BLUE = colors.HexColor("#3a56d4")
PURPLE = colors.HexColor("#7048e8")
LIGHT = colors.HexColor("#eef1fb")
PRIORITY_COLORS = {"High": colors.HexColor("#c92a2a"), "Medium": colors.HexColor("#b35c00"),
                   "Low": colors.HexColor("#2b6cb0")}


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], textColor=NAVY, fontSize=20, spaceAfter=4),
        "subtitle": ParagraphStyle("st", parent=base["Normal"], textColor=colors.grey, alignment=TA_CENTER,
                                   fontSize=9),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=10,
                             spaceAfter=4),
        "body": ParagraphStyle("b", parent=base["Normal"], fontSize=9, leading=12),
        "small": ParagraphStyle("s", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.grey),
        "cell": ParagraphStyle("c", parent=base["Normal"], fontSize=8.5, leading=11),
        "big": ParagraphStyle("big", parent=base["Normal"], fontSize=22, leading=26, alignment=TA_CENTER,
                              textColor=BLUE, fontName="Helvetica-Bold"),
        "label": ParagraphStyle("lbl", parent=base["Normal"], fontSize=8.5, alignment=TA_CENTER,
                                textColor=colors.grey),
    }


def _p(text, style):
    return Paragraph(escape(str(text)), style)


def _grid(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d5e6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 9)]
    t.setStyle(TableStyle(style))
    return t


def generate_pdf_report(analysis: dict) -> bytes:
    """``analysis`` is the dict returned by ``Analysis.to_dict()``."""
    s = _styles()
    d = analysis["details"]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title="Resume Analysis Report",
                            author="Smart Resume Analyzer")
    story = []
    created = datetime.fromisoformat(analysis["created_at"].rstrip("Z"))

    story.append(_p("Resume Analysis Report", s["title"]))
    story.append(_p(f"Smart Resume Analyzer with AI-Based Feedback  |  Generated "
                    f"{created.strftime('%d %b %Y, %H:%M')} UTC", s["subtitle"]))
    story.append(Spacer(1, 8))

    info_rows = [
        ["File", analysis["original_filename"]],
        ["Target job role", analysis["target_role_title"]],
        ["Candidate", d.get("candidate", {}).get("name") or "Not identified"],
        ["Analysis date", created.strftime("%d %B %Y")],
    ]
    t = Table([[_p(k, s["cell"]), _p(v, s["cell"])] for k, v in info_rows], colWidths=[40 * mm, 138 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), LIGHT), ("GRID", (0, 0), (-1, -1), 0.4,
                                                                        colors.HexColor("#d0d5e6"))]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Headline scores
    cards = Table([
        [_p(f"{analysis['resume_score']}/100", s["big"]), _p(f"{analysis['ats_score']}/100", s["big"]),
         _p(f"{analysis['keyword_match_percentage']:g}%", s["big"])],
        [_p(f"Resume score - {analysis['score_category']}", s["label"]),
         _p("Estimated ATS compatibility", s["label"]), _p("Role keyword match", s["label"])],
    ], colWidths=[59 * mm] * 3)
    cards.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, BLUE), ("INNERGRID", (0, 0), (-1, -1), 0.3,
                                                                     colors.HexColor("#d0d5e6")),
                               ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("TOPPADDING", (0, 0), (-1, -1), 6),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(cards)

    # Parameter breakdown
    story.append(_p("Resume Score Breakdown", s["h2"]))
    rows = [["Parameter", "Score", "Evidence found", "Gaps"]]
    for p in d["resume_score"]["parameters"]:
        rows.append([
            _p(p["label"], s["cell"]),
            _p(f"{p['score']:g} / {p['max_score']}", s["cell"]),
            _p("; ".join(p["evidence"]) or "-", s["cell"]),
            _p("; ".join(p["missing"]) or "-", s["cell"]),
        ])
    rows.append([_p("Total", s["cell"]), _p(f"{analysis['resume_score']} / 100", s["cell"]), "", ""])
    story.append(_grid(rows, [32 * mm, 20 * mm, 66 * mm, 60 * mm]))

    # ATS components
    story.append(_p("Estimated ATS Compatibility", s["h2"]))
    rows = [["Component", "Weight", "Score", "Weighted"]]
    for c in d["ats"]["components"]:
        rows.append([_p(c["name"], s["cell"]), f"{int(c['weight'] * 100)}%", f"{c['score']}/100",
                     f"{c['weighted']:g}"])
    rows.append([_p("Estimated ATS score", s["cell"]), "100%", "", f"{analysis['ats_score']}"])
    story.append(_grid(rows, [80 * mm, 30 * mm, 34 * mm, 34 * mm]))

    # Skills
    sk = d["skills"]
    story.append(_p(f"Skill Analysis - {analysis['target_role_title']}", s["h2"]))
    story.append(_p(f"Matched keywords ({len(sk['matched'])}): " + (", ".join(sk["matched"]) or "none"), s["body"]))
    story.append(Spacer(1, 3))
    story.append(_p(f"Missing keywords ({len(sk['missing'])}): " + (", ".join(sk["missing"]) or "none"), s["body"]))
    story.append(Spacer(1, 3))
    story.append(_p("Other technical skills detected: " + (", ".join(sk["additional_skills"]) or "none"),
                    s["body"]))
    story.append(Spacer(1, 2))
    story.append(_p("A missing keyword means the term was not found in the text; it does not mean the candidate "
                    "lacks the skill.", s["small"]))

    # Feedback
    story.append(_p("Improvement Suggestions", s["h2"]))
    rows = [["Priority", "Suggestion", "Details"]]
    for f in analysis["feedback"]:
        pr = ParagraphStyle("pr", parent=s["cell"], textColor=PRIORITY_COLORS.get(f["priority"], NAVY),
                            fontName="Helvetica-Bold")
        details = (f"<b>Issue:</b> {escape(f['issue'])}<br/><b>Evidence:</b> {escape(f['evidence'])}"
                   f"<br/><b>Recommendation:</b> {escape(f['recommendation'])}"
                   f"<br/><i>{escape(f['explanation'])}</i>")
        rows.append([Paragraph(f["priority"], pr), _p(f"{f['title']} ({f['category']})", s["cell"]),
                     Paragraph(details, s["cell"])])
    if len(rows) == 1:
        rows.append(["-", "No improvement suggestions were triggered.", ""])
    story.append(_grid(rows, [18 * mm, 44 * mm, 116 * mm]))

    # Methodology
    story.append(_p("Scoring Methodology & Disclaimer", s["h2"]))
    story.append(_p(
        "Resume score: six rule-based parameters - structure (20), skills (20), education (15), projects (15), "
        "contact (15) and completeness (15). Score categories (85+ Excellent, 70+ Good, 50+ Needs Improvement, "
        "below 50 Significant Improvement Needed) are defined by this application, not by any industry "
        f"standard. ATS score: {d['ats']['formula']}. {d['ats']['disclaimer']} Keyword dictionaries are "
        "editable starter lists, not definitive hiring requirements. NLP backend: "
        f"{d.get('nlp', {}).get('backend', 'spaCy')}.", s["small"]))

    doc.build(story)
    return buf.getvalue()
