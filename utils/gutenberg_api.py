"""Project Gutenberg RapidAPI client — browse subjects, books, and fetch passages."""
import os
import re
import warnings
import requests
from urllib3.exceptions import InsecureRequestWarning

# Corporate proxy re-signs TLS with its own CA which Python's certifi doesn't trust.
# Suppress the resulting warning and disable verification for these external calls only.
warnings.filterwarnings("ignore", category=InsecureRequestWarning)
_VERIFY = False

_BASE    = "https://project-gutenberg-free-books-api1.p.rapidapi.com"
_API_KEY = os.getenv("RAPIDAPI_KEY", "4410d21c1dmshd64191b3be17f7cp1173aejsn8db76947ead2")
_HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "project-gutenberg-free-books-api1.p.rapidapi.com",
    "x-rapidapi-key": _API_KEY,
}
_TIMEOUT = 12


def get_subjects() -> list[str]:
    """Return the list of available subjects."""
    r = requests.get(f"{_BASE}/subjects", headers=_HEADERS, timeout=_TIMEOUT, verify=_VERIFY)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        subjects = [s if isinstance(s, str) else s.get("name", str(s)) for s in data]
    else:
        raw = data.get("subjects") or data.get("data") or data.get("results") or []
        subjects = [s if isinstance(s, str) else s.get("name", str(s)) for s in raw]
    return sorted(s.strip() for s in subjects if s)


def get_books(subject: str = "", search: str = "") -> list[dict]:
    """Return books filtered by subject or search query."""
    params: dict = {}
    if subject:
        params["subject"] = subject
    if search:
        params["search"] = search
    r = requests.get(f"{_BASE}/books", headers=_HEADERS, params=params, timeout=_TIMEOUT, verify=_VERIFY)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    for key in ("books", "data", "results", "items"):
        if key in data:
            return data[key]
    return []


def _extract_text(data: dict) -> str:
    """Pull the raw text string from whatever field the API returns it in."""
    for key in ("text", "content", "body", "chapter", "full_text", "rawText"):
        val = data.get(key)
        if isinstance(val, str) and len(val) > 100:
            return val
    return ""


def _clean(text: str) -> str:
    """Strip Gutenberg boilerplate header / footer and normalise whitespace."""
    # Remove everything before "*** START OF" marker
    start = re.search(r"\*{3}\s*START OF (THIS|THE) PROJECT GUTENBERG", text, re.I)
    if start:
        text = text[start.end():]
    # Remove everything after "*** END OF" marker
    end = re.search(r"\*{3}\s*END OF (THIS|THE) PROJECT GUTENBERG", text, re.I)
    if end:
        text = text[: end.start()]
    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _trim_to_passage(text: str, max_words: int = 450) -> str:
    """Return the first ~max_words words, ending on a sentence boundary."""
    text = _clean(text)
    words = text.split()
    if len(words) <= max_words:
        return text
    chunk = " ".join(words[:max_words])
    # Try to end on a sentence boundary in the last 25 % of the chunk
    cutoff_zone = chunk[int(len(chunk) * 0.75):]
    for end_char in (".", "!", "?"):
        idx = cutoff_zone.rfind(end_char)
        if idx != -1:
            absolute = int(len(chunk) * 0.75) + idx + 1
            return chunk[:absolute].strip()
    return chunk.strip()


def _gutenberg_direct(book_id: int, max_words: int = 450) -> str:
    """Fallback: fetch raw .txt directly from Gutenberg CDN."""
    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    try:
        r = requests.get(url, timeout=15, verify=_VERIFY)
        r.raise_for_status()
        return _trim_to_passage(r.text, max_words)
    except Exception:
        return ""


def get_book_passage(book: dict, max_words: int = 450) -> str:
    """
    Fetch an opening passage for a book dict returned by get_books().
    Tries the RapidAPI /books/{id} endpoint first, then falls back to
    the Gutenberg CDN .txt file.
    """
    book_id = book.get("id") or book.get("book_id") or book.get("gutenberg_id")
    if not book_id:
        return ""

    # ── Try RapidAPI book detail endpoint ─────────────────────────────────────
    try:
        r = requests.get(f"{_BASE}/books/{book_id}", headers=_HEADERS, timeout=_TIMEOUT, verify=_VERIFY)
        if r.ok:
            data = r.json()
            text = _extract_text(data if isinstance(data, dict) else {})
            if text:
                return _trim_to_passage(text, max_words)
    except Exception:
        pass

    # ── Fallback: direct Gutenberg CDN ────────────────────────────────────────
    try:
        gutenberg_num = int(str(book_id).strip())
        return _gutenberg_direct(gutenberg_num, max_words)
    except (ValueError, TypeError):
        pass

    return ""
