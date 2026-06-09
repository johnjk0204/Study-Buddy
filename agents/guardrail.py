"""Input guardrail agent — screens for PII and inappropriate content."""
import re
from utils.llm import call_claude, extract_json
from graph.state import PassageState


# ── PII regex patterns ────────────────────────────────────────────────────────

PII_PATTERNS: dict[str, str] = {
    "email address": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone number": (
        r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    "Social Security Number": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit card number": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "IP address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "date of birth": (
        r"\b(0?[1-9]|1[0-2])[/\-](0?[1-9]|[12]\d|3[01])[/\-](19|20)\d{2}\b"
    ),
    "street address": (
        r"\b\d+\s+[A-Za-z]+\s+"
        r"(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b"
    ),
    "passport number": r"\b[A-Z]{1,2}\d{6,9}\b",
}


# ── Content safety prompt ─────────────────────────────────────────────────────

_SAFETY_SYSTEM = """You are a content safety checker for a school education platform (students aged 6–18).
Decide whether the passage is safe for classroom use.

Flag ONLY genuinely inappropriate content:
- Graphic violence or gore
- Sexual or adult content
- Hate speech or discrimination
- Drug / alcohol glorification
- Cyberbullying or personal harassment

Educational topics (historical wars, biology, chemistry, current events, health) are SAFE.

Respond with JSON only — no extra text:
{
  "is_safe": true,
  "issues": []
}
or
{
  "is_safe": false,
  "issues": ["specific issue 1", "specific issue 2"]
}"""


def _check_pii(text: str) -> list[str]:
    found = []
    for label, pattern in PII_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(f"Personal information detected: {label}")
    return found


def _check_content_safety(text: str) -> tuple[bool, list[str]]:
    try:
        raw = call_claude(
            f"Check this passage for school safety:\n\n{text}",
            _SAFETY_SYSTEM,
            max_tokens=512,
        )
        result = extract_json(raw)
        return result.get("is_safe", True), result.get("issues", [])
    except Exception:
        return True, []  # default safe if Claude call fails


async def async_guardrail_agent(state: PassageState) -> dict:
    """Async version — used by the parallel LangGraph graph."""
    from utils.llm import acall_claude
    passage = state["passage"].strip()
    if len(passage) < 20:
        return {"guardrail_status": "blocked", "guardrail_issues": [
            "The passage is too short. Please provide a meaningful text to analyze."
        ]}
    pii_issues = _check_pii(passage)
    try:
        raw = await acall_claude(
            f"Check this passage for school safety:\n\n{passage}",
            _SAFETY_SYSTEM,
            max_tokens=512,
        )
        result = extract_json(raw)
        is_safe = result.get("is_safe", True)
        content_issues = result.get("issues", [])
    except Exception:
        is_safe, content_issues = True, []
    all_issues = pii_issues + content_issues
    if all_issues or not is_safe:
        return {"guardrail_status": "blocked",
                "guardrail_issues": all_issues or ["Content not appropriate for educational use."]}
    return {"guardrail_status": "pass", "guardrail_issues": []}


def guardrail_agent(state: PassageState) -> dict:
    passage = state["passage"].strip()

    if len(passage) < 20:
        return {
            "guardrail_status": "blocked",
            "guardrail_issues": [
                "The passage is too short. Please provide a meaningful text to analyze."
            ],
        }

    pii_issues = _check_pii(passage)
    is_safe, content_issues = _check_content_safety(passage)

    all_issues = pii_issues + content_issues

    if all_issues or not is_safe:
        return {
            "guardrail_status": "blocked",
            "guardrail_issues": all_issues
            or ["Content is not appropriate for educational use."],
        }

    return {"guardrail_status": "pass", "guardrail_issues": []}
