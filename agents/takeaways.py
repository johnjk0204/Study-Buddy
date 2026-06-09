"""Takeaway + Facts Agent — grade-aware content using llama-3.3-70b."""
from utils.llm import acall_claude, call_claude, extract_json, MODEL_BEST
from graph.state import PassageState


_YOUNG_SYSTEM = """You are a fun teacher sharing amazing things with children aged 5-7.
Generate simple takeaways and wow facts a 6-year-old will love.

Return ONLY valid JSON:
{
  "takeaways": [
    {
      "point": "One simple thing to remember (max 10 easy words)",
      "why_important": "Because [one very simple sentence connecting to everyday life]",
      "emoji": "one fun emoji"
    }
  ],
  "facts": [
    {
      "fact": "Did you know that [amazing fact using simple words and a fun comparison]?",
      "emoji": "one fun emoji",
      "wow_factor": "That is [simple reason it is amazing, like 'that is as big as 10 school buses!']"
    }
  ]
}

Generate exactly 5 takeaways and 5 facts.
Use ONLY simple words a 6-year-old knows. Include fun size comparisons like 'as tall as your house'."""

_MIDDLE_SYSTEM = """You are an enthusiastic teacher for students aged 8-11.
Generate clear takeaways and interesting facts.

Return ONLY valid JSON:
{
  "takeaways": [
    {
      "point": "Clear learning point starting with a verb (max 15 words)",
      "why_important": "One sentence connecting to everyday life or a future job",
      "emoji": "relevant emoji"
    }
  ],
  "facts": [
    {
      "fact": "Did you know that [surprising fact with a specific number or comparison]?",
      "emoji": "relevant emoji",
      "wow_factor": "One sentence explaining why this is impressive"
    }
  ]
}

Generate exactly 5 takeaways and 5 facts.
Facts must include specific numbers, names, or size comparisons. Keep language simple but engaging."""

_SENIOR_SYSTEM = """You are an enthusiastic teacher and science communicator for students aged 12-18.
Generate rich takeaways and genuinely surprising facts.

Return ONLY valid JSON:
{
  "takeaways": [
    {
      "point": "Actionable learning point starting with a verb",
      "why_important": "Real-world relevance — connect to a job, daily life, or future study",
      "emoji": "relevant emoji"
    }
  ],
  "facts": [
    {
      "fact": "Did you know that [surprising, specific fact with a real number, date, name, or world-record comparison]?",
      "emoji": "relevant emoji",
      "wow_factor": "One sentence: why this fact is genuinely mind-blowing"
    }
  ]
}

Generate exactly 5 takeaways and 5 facts.
Every fact MUST contain specific numbers, dates, names, or comparisons — not vague statements."""


def _pick_system(state) -> str:
    g = (state.get("requested_grade") or "").lower()
    if "1" in g or "2" in g:
        return _YOUNG_SYSTEM
    if "3" in g or "4" in g or "5" in g:
        return _MIDDLE_SYSTEM
    return _SENIOR_SYSTEM


def _fallback(state: PassageState) -> dict:
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    concepts = state.get("key_concepts") or []
    g = (state.get("requested_grade") or "").lower()
    young = "1" in g or "2" in g
    verbs = ["Remember", "Learn", "Find out", "Think about", "Look at"] if young else \
            ["Understand", "Remember", "Explain", "Connect", "Apply"]
    takeaways = [
        {"point": f"{verbs[i % len(verbs)]} {c}.",
         "why_important": f"Because it helps us understand {topic}.",
         "emoji": "⭐" if young else "✅"}
        for i, c in enumerate(concepts[:5])
    ]
    while len(takeaways) < 5:
        takeaways.append({"point": f"{'Look for' if young else 'Connect'} {topic} in your world.",
                          "why_important": "It is all around us!",
                          "emoji": "🌟"})
    facts = [{"fact": f"Did you know that {topic} is amazing?",
              "emoji": "💡",
              "wow_factor": f"It is one of the most interesting things in {subject}!"}] * 5
    return {"key_takeaways": takeaways[:5], "did_you_know_facts": facts[:5]}


async def async_takeaways_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = await acall_claude(
            f"Generate takeaways and facts for:\n\n{context}",
            _pick_system(state), max_tokens=1800, model=MODEL_BEST,
        )
        result = extract_json(raw)
        return {"key_takeaways": result.get("takeaways", []),
                "did_you_know_facts": result.get("facts", [])}
    except Exception:
        return _fallback(state)


def takeaways_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = call_claude(
            f"Generate takeaways and facts for:\n\n{context}",
            _pick_system(state), max_tokens=1800, model=MODEL_BEST,
        )
        result = extract_json(raw)
        return {"key_takeaways": result.get("takeaways", []),
                "did_you_know_facts": result.get("facts", [])}
    except Exception:
        return _fallback(state)
