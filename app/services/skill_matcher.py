"""Module 3 - technical skill extraction and role-based skill matching.

Matching is phrase-aware and uses technical-term boundaries so that:
* "Java" does not match inside "JavaScript", and "SQL" does not match inside "MySQL"
* "C++", "C#", "Node.js" and "CI/CD" are matched with their punctuation
* ambiguous short aliases ("ML", "AI", "JS") need supporting context nearby
"""
import json
import re
from functools import lru_cache

from .text_preprocessor import normalize_for_matching

_LEFT = r"(?<![a-z0-9+#])"
_RIGHT = r"(?![a-z0-9+#]|\.[a-z0-9])"  # "node.js." at sentence end is fine; "vue.config" is not "vue"
CONTEXT_WINDOW = 120


def _alias_pattern(alias: str) -> re.Pattern:
    parts = [re.escape(p) for p in alias.lower().split()]
    return re.compile(_LEFT + r"[\s\-]*".join(parts) + _RIGHT) if len(parts) > 1 else re.compile(
        _LEFT + parts[0] + _RIGHT
    )


@lru_cache(maxsize=4)
def load_skill_dictionary(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    skills = []
    for entry in raw["skills"]:
        skills.append({
            "name": entry["name"],
            "category": entry["category"],
            "patterns": [(alias.lower(), _alias_pattern(alias)) for alias in entry["aliases"]],
        })
    context = {k.lower(): set(v) for k, v in raw.get("context_aliases", {}).items()}
    return {"skills": skills, "context": context, "by_name": {s["name"]: s for s in skills}}


@lru_cache(maxsize=4)
def load_roles(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["roles"]


def _context_ok(text: str, start: int, end: int, context_words: set) -> bool:
    window = text[max(0, start - CONTEXT_WINDOW): end + CONTEXT_WINDOW]
    words = set(re.findall(r"[a-z][a-z\-]*", window))
    return bool(words & context_words)


def detect_skills(text: str, dictionary: dict) -> dict:
    """Return {skill_name: {"category", "matched_alias", "count"}} for skills found in text."""
    norm = normalize_for_matching(text)
    found = {}
    for skill in dictionary["skills"]:
        total, first_alias = 0, None
        for alias, pattern in skill["patterns"]:
            for m in pattern.finditer(norm):
                if alias in dictionary["context"] and not _context_ok(
                    norm, m.start(), m.end(), dictionary["context"][alias]
                ):
                    continue
                total += 1
                first_alias = first_alias or alias
        if total:
            found[skill["name"]] = {"category": skill["category"], "matched_alias": first_alias, "count": total}
    return found


def skill_in_text(skill_name: str, text: str, dictionary: dict) -> bool:
    skill = dictionary["by_name"].get(skill_name)
    if not skill or not text:
        return False
    return skill_name in detect_skills(text, {"skills": [skill], "context": dictionary["context"]})


def group_by_category(skills: dict) -> dict:
    grouped = {}
    for name, info in sorted(skills.items(), key=lambda kv: kv[0].lower()):
        grouped.setdefault(info["category"], []).append(name)
    return grouped


def match_role_skills(detected: dict, role: dict) -> dict:
    """Compare detected skills against a role's reference keywords (skill-gap analysis)."""
    reference = role["keywords"]
    matched = [k for k in reference if k in detected]
    missing = [k for k in reference if k not in detected]
    core = role.get("core_keywords", [])
    pct = round(100 * len(matched) / len(reference), 1) if reference else 0.0
    return {
        "reference_keywords": reference,
        "matched": matched,
        "missing": missing,
        "core_missing": [k for k in core if k in missing],
        "match_percentage": pct,
        "coverage_details": [
            {
                "keyword": k,
                "matched": k in detected,
                "occurrences": detected.get(k, {}).get("count", 0),
                "matched_as": detected.get(k, {}).get("matched_alias"),
                "core": k in core,
            }
            for k in reference
        ],
        "additional_skills": sorted(k for k in detected if k not in reference),
    }
