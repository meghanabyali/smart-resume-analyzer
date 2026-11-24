"""Module 1/3 - text normalisation and basic NLP (spaCy + NLTK).

The NLP models are loaded lazily and degrade gracefully:
* spaCy ``en_core_web_sm`` (lemmas, NER, noun chunks) -> falls back to ``spacy.blank('en')``
* NLTK stopwords corpus -> falls back to a built-in stopword list
"""
import logging
import os
import re
import unicodedata
from functools import lru_cache

import nltk
from nltk.probability import FreqDist
from nltk.tokenize import RegexpTokenizer
from nltk.util import ngrams

from ..config import DATA_DIR

log = logging.getLogger(__name__)

_local_nltk = str(DATA_DIR / "nltk_data")
if os.path.isdir(_local_nltk) and _local_nltk not in nltk.data.path:
    nltk.data.path.insert(0, _local_nltk)

BULLET_CHARS = "•●▪◦➢➤►▶✓✔■□◆◇○-*–·"
_BULLET_RE = re.compile(r"^\s*[•●▪◦➢➤►▶✓✔■□◆◇○*–·]\s*|^\s*-\s+")
_LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", " ": " ", "​": "",
              "’": "'", "‘": "'", "“": '"', "”": '"', "–": "–", "": "•"}

# Tokens keep technical punctuation so that C++, C#, Node.js and CI/CD survive.
_TOKENIZER = RegexpTokenizer(r"[A-Za-z][A-Za-z0-9]*(?:[.+#/\-][A-Za-z0-9+#]+)*\+*#?|\d+(?:\.\d+)?%?")

_FALLBACK_STOPWORDS = set("""
a about above after again against all am an and any are as at be because been before being below between
both but by can could did do does doing down during each few for from further had has have having he her
here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not
now of off on once only or other our ours ourselves out over own same she should so some such than that the
their theirs them themselves then there these they this those through to too under until up very was we were
what when where which while who whom why will with would you your yours yourself yourselves
""".split())

# Resume boilerplate that carries no analytical meaning.
RESUME_STOPWORDS = {
    "resume", "curriculum", "vitae", "cv", "name", "email", "phone", "mobile", "address", "linkedin",
    "github", "com", "www", "http", "https", "in", "using", "used", "etc", "also", "various", "responsible",
    "work", "worked", "year", "years", "month", "months", "present", "current", "jan", "feb", "mar", "apr",
    "may", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "january", "february", "march", "april",
    "june", "july", "august", "september", "october", "november", "december", "skills", "projects",
    "education", "experience", "summary", "objective", "profile", "certifications", "achievements",
}


@lru_cache(maxsize=1)
def get_stopwords() -> frozenset:
    try:
        from nltk.corpus import stopwords

        words = set(stopwords.words("english"))
    except LookupError:
        words = set(_FALLBACK_STOPWORDS)
    return frozenset(words | RESUME_STOPWORDS)


@lru_cache(maxsize=1)
def get_nlp():
    """Return a spaCy pipeline (full English model if installed)."""
    import spacy

    try:
        nlp = spacy.load("en_core_web_sm", disable=["textcat"])
        nlp.max_length = 200_000
        return nlp
    except OSError:
        log.warning("spaCy model en_core_web_sm not installed - using a blank English tokenizer.")
        return spacy.blank("en")


def nlp_backend_name() -> str:
    nlp = get_nlp()
    name = nlp.meta.get("name", "blank")
    return f"spaCy {nlp.meta.get('lang', 'en')}_{name}" if name != "blank" else "spaCy blank tokenizer"


def has_statistical_model() -> bool:
    return "ner" in get_nlp().pipe_names


# ------------------------------------------------------------------ cleaning
def clean_text(raw: str) -> str:
    """Normalise unicode, bullets and whitespace while keeping line structure."""
    text = unicodedata.normalize("NFKC", raw)
    for bad, good in _LIGATURES.items():
        text = text.replace(bad, good)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[  - ]+", " ", line).strip()
        if _BULLET_RE.match(line):
            line = "• " + _BULLET_RE.sub("", line, count=1).strip()
            if line == "•":
                continue
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def is_bullet(line: str) -> bool:
    return line.startswith("• ")


def strip_bullet(line: str) -> str:
    return line[2:].strip() if is_bullet(line) else line


def normalize_for_matching(text: str) -> str:
    """Lower-case, single-spaced text for keyword matching (punctuation preserved)."""
    text = text.lower().replace("•", " ")
    return re.sub(r"\s+", " ", text).strip()


# ------------------------------------------------------------------ tokens
def tokenize(text: str) -> list:
    return _TOKENIZER.tokenize(text)


def content_tokens(text: str) -> list:
    """Lower-cased tokens without stopwords or pure numbers."""
    stop = get_stopwords()
    return [t.lower() for t in tokenize(text) if t.lower() not in stop and not t[0].isdigit() and len(t) > 1]


def lemmatize_tokens(text: str) -> list:
    """Lemmas of content words using spaCy (falls back to lower-cased tokens)."""
    nlp = get_nlp()
    if "lemmatizer" not in nlp.pipe_names:
        return content_tokens(text)
    stop = get_stopwords()
    doc = nlp(text[:100_000])
    return [
        tok.lemma_.lower()
        for tok in doc
        if tok.is_alpha and len(tok) > 1 and tok.lemma_.lower() not in stop and tok.text.lower() not in stop
    ]


def extract_top_keywords(text: str, limit: int = 15) -> list:
    """Most frequent meaningful terms and two-word phrases (NLTK FreqDist + spaCy lemmas)."""
    lemmas = lemmatize_tokens(text)
    freq = FreqDist(lemmas)
    bigram_freq = FreqDist(" ".join(bg) for bg in ngrams(lemmas, 2))

    scored = [(term, count) for term, count in freq.items() if count >= 2]
    scored += [(term, count * 1.5) for term, count in bigram_freq.items() if count >= 2]
    scored.sort(key=lambda x: (-x[1], x[0]))

    keywords, seen = [], set()
    for term, score in scored:
        if term in seen:
            continue
        seen.add(term)
        keywords.append({"term": term, "frequency": int(round(score if " " not in term else score / 1.5))})
        if len(keywords) >= limit:
            break
    return keywords


def extract_noun_phrases(text: str, limit: int = 12) -> list:
    """Noun chunks from spaCy's dependency parser (empty if parser unavailable)."""
    nlp = get_nlp()
    if "parser" not in nlp.pipe_names:
        return []
    doc = nlp(text[:60_000])
    stop = get_stopwords()
    freq = FreqDist()
    for chunk in doc.noun_chunks:
        words = [t.lemma_.lower() for t in chunk if t.is_alpha and t.text.lower() not in stop]
        if len(words) >= 2:
            freq[" ".join(words)] += 1
    return [phrase for phrase, _ in freq.most_common(limit)]
