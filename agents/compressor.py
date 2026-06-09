"""Passage compressor — shrinks the user's passage before downstream agents see it.

Only kicks in when the passage exceeds 120 words.  All subsequent agents read
`compressed_passage` instead of the raw `passage`, cutting input tokens by
roughly 40-50 % and making every API call finish faster.
"""
from utils.llm import call_claude
from graph.state import PassageState


_SYSTEM = (
    "You are a precise educational-text compressor. "
    "Compress the passage to about 50 % of its original length. "
    "Rules:\n"
    "- Keep ALL key concepts, facts, names, dates, numbers, and cause-effect relationships.\n"
    "- Remove filler phrases, redundant restatements, and overly wordy transitions.\n"
    "- Preserve technical vocabulary exactly.\n"
    "- Return ONLY the compressed text — no headings, no explanation."
)


def compressor_agent(state: PassageState) -> dict:
    passage = state["passage"].strip()

    # Skip compression for short passages — overhead isn't worth it.
    if len(passage.split()) < 120:
        return {"compressed_passage": passage}

    try:
        compressed = call_claude(
            f"Compress this educational passage to ~50 % of its length:\n\n{passage}",
            _SYSTEM,
            max_tokens=1024,
        )
        # Safety-net: never return something longer than the original.
        if len(compressed.split()) >= len(passage.split()):
            return {"compressed_passage": passage}
        return {"compressed_passage": compressed}
    except Exception:
        return {"compressed_passage": passage}
