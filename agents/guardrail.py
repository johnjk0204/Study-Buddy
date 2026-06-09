"""Input guardrail — screens for PII and inappropriate content."""
import re
from utils.llm import acall_claude, call_claude, extract_json, MODEL_FAST
from graph.state import PassageState

PII_PATTERNS: dict[str, str] = {
    "email address":      r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone number":       r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "Social Security Number": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit card number": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "IP address":         r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "street address":     r"\b\d+\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b",
}

_SAFETY_SYSTEM = (
    "You are a content safety checker for a school platform (ages 6-18). "
    "Flag ONLY genuinely inappropriate content: graphic violence, sexual content, "
    "hate speech, drug glorification, cyberbullying. "
    "Educational topics (wars, biology, chemistry, history, health) are SAFE. "
    "Respond with JSON only: {\"is_safe\": true, \"issues\": []}"
)


def _check_pii(text: str) -> list[str]:
    return [f"Personal information detected: {label}"
            for label, pat in PII_PATTERNS.items()
            if re.search(pat, text, re.IGNORECASE)]


async def async_guardrail_agent(state: PassageState) -> dict:
    passage = state["passage"].strip()
    if len(passage) < 20:
        return {"guardrail_status": "blocked",
                "guardrail_issues": ["Passage is too short. Please provide a meaningful text."]}
    pii_issues = _check_pii(passage)
    try:
        raw = await acall_claude(
            f"Check this passage for school safety:\n\n{passage}",
            _SAFETY_SYSTEM, max_tokens=256, model=MODEL_FAST,
        )
        result   = extract_json(raw)
        is_safe  = result.get("is_safe", True)
        c_issues = result.get("issues", [])
    except Exception:
        is_safe, c_issues = True, []
    all_issues = pii_issues + c_issues
    if all_issues or not is_safe:
        return {"guardrail_status": "blocked",
                "guardrail_issues": all_issues or ["Content not appropriate for educational use."]}
    return {"guardrail_status": "pass", "guardrail_issues": []}


def guardrail_agent(state: PassageState) -> dict:
    passage = state["passage"].strip()
    if len(passage) < 20:
        return {"guardrail_status": "blocked",
                "guardrail_issues": ["Passage is too short. Please provide a meaningful text."]}
    pii_issues = _check_pii(passage)
    try:
        raw = call_claude(
            f"Check this passage for school safety:\n\n{passage}",
            _SAFETY_SYSTEM, max_tokens=256, model=MODEL_FAST,
        )
        result   = extract_json(raw)
        is_safe  = result.get("is_safe", True)
        c_issues = result.get("issues", [])
    except Exception:
        is_safe, c_issues = True, []
    all_issues = pii_issues + c_issues
    if all_issues or not is_safe:
        return {"guardrail_status": "blocked",
                "guardrail_issues": all_issues or ["Content not appropriate for educational use."]}
    return {"guardrail_status": "pass", "guardrail_issues": []}
