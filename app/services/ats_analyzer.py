"""Module 3 - estimated ATS compatibility score (0-100).

ATS = 60% role keyword coverage + 20% parseability + 20% structural compatibility
(weights configurable). This is a deterministic *estimate* - it is not
produced by, or guaranteed to match, any commercial ATS.
"""
DEFAULT_ATS_WEIGHTS = {"keyword_coverage": 0.60, "parseability": 0.20, "structure": 0.20}
STANDARD_SECTIONS = ("education", "skills", "projects", "experience", "internships", "summary")


def _component(name, score, checks, explanation):
    return {"name": name, "score": int(round(max(0, min(100, score)))), "checks": checks, "explanation": explanation}


def calculate_parseability(document: dict, info: dict) -> dict:
    checks, score = [], 0
    words = document["word_count"]

    score += 40
    checks.append({"label": "Text layer extracted successfully", "passed": True, "points": 40})

    dense = words >= 150
    score += 20 if dense else 10
    checks.append({"label": f"Sufficient machine-readable text ({words} words)", "passed": dense,
                   "points": 20 if dense else 10})

    text = info["clean_text"]
    garbled = sum(1 for ch in text if ch == "�") + text.count("(cid:")
    clean = garbled <= 2
    score += 20 if clean else 5
    checks.append({"label": "No garbled/encoding artefacts", "passed": clean, "points": 20 if clean else 5})

    layout = document.get("layout", {})
    issues = []
    if layout.get("multi_column"):
        issues.append("multi-column layout")
    if layout.get("table_count", 0) > 2:
        issues.append(f"{layout['table_count']} tables")
    if layout.get("image_count", 0) > 3:
        issues.append(f"{layout['image_count']} images/graphics")
    simple = not issues
    score += 20 if simple else 8
    checks.append({"label": "Simple single-column layout" if simple else "Complex layout: " + ", ".join(issues),
                   "passed": simple, "points": 20 if simple else 8})

    return _component("Parseability", score, checks,
                      "How reliably an automated parser can read the document's text in order.")


def calculate_structural_compatibility(document: dict, info: dict) -> dict:
    checks, score = [], 0
    found = [s for s in info["section_order"] if s in STANDARD_SECTIONS]
    pts = min(40, 10 * len(found))
    score += pts
    checks.append({"label": f"Standard headings recognised ({len(found)})", "passed": len(found) >= 4, "points": pts})

    cand = info["candidate"]
    contact_pts = (15 if cand.get("email") else 0) + (15 if cand.get("phone") else 0)
    score += contact_pts
    checks.append({"label": "Email and phone in plain text", "passed": contact_pts == 30, "points": contact_pts})

    good_len = document["page_count"] <= 2
    score += 15 if good_len else 5
    checks.append({"label": f"Length of {document['page_count']} page(s)", "passed": good_len,
                   "points": 15 if good_len else 5})

    bullets = info.get("bullet_line_count", 0)
    bullet_pts = 15 if bullets >= 4 else 8 if bullets >= 1 else 0
    score += bullet_pts
    checks.append({"label": f"Bullet-point formatting ({bullets} bullet lines)", "passed": bullets >= 4,
                   "points": bullet_pts})

    return _component("Structural compatibility", score, checks,
                      "Whether the resume uses conventions ATS parsers expect: standard headings, plain-text "
                      "contact details, 1-2 pages and bullet points.")


def calculate_ats_score(document: dict, info: dict, role_match: dict, weights=None) -> dict:
    w = {**DEFAULT_ATS_WEIGHTS, **(weights or {})}
    coverage = _component(
        "Role keyword coverage",
        role_match["match_percentage"],
        [{"label": f"{len(role_match['matched'])} of {len(role_match['reference_keywords'])} reference keywords found",
          "passed": role_match["match_percentage"] >= 60, "points": round(role_match["match_percentage"])}],
        "Share of the selected role's reference keywords that appear in the resume.",
    )
    parse = calculate_parseability(document, info)
    struct = calculate_structural_compatibility(document, info)

    total = (w["keyword_coverage"] * coverage["score"] + w["parseability"] * parse["score"]
             + w["structure"] * struct["score"])
    components = [
        {**coverage, "weight": w["keyword_coverage"], "key": "keyword_coverage"},
        {**parse, "weight": w["parseability"], "key": "parseability"},
        {**struct, "weight": w["structure"], "key": "structure"},
    ]
    for comp in components:
        comp["weighted"] = round(comp["score"] * comp["weight"], 1)
    return {
        "score": int(round(max(0, min(100, total)))),
        "components": components,
        "formula": " + ".join(f"{int(c['weight'] * 100)}% {c['name'].lower()}" for c in components),
        "disclaimer": "Estimated ATS compatibility based on transparent rules. It is not a score from, or a "
                      "guarantee of performance in, any commercial Applicant Tracking System.",
    }
