"""Did-You-Know agent — generates surprising, age-appropriate facts from the passage."""
from utils.llm import call_claude, extract_json
from graph.state import PassageState


_SYSTEM = """You are an enthusiastic teacher who loves sharing amazing facts with school students.
Generate interesting "Did You Know?" facts that are connected to the passage topic.

Each fact must:
- Start with "Did you know that…"
- Be surprising or counterintuitive
- Be 100% accurate and age-appropriate
- Use simple, exciting language

Respond with JSON only — no extra text:
{
  "facts": [
    {
      "fact": "Did you know that...",
      "emoji": "one relevant emoji",
      "wow_factor": "one sentence explaining why this blows your mind"
    }
  ]
}

Generate exactly 6 facts."""


def did_you_know_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )
    try:
        raw = call_claude(
            f"Generate Did You Know facts for this educational content:\n\n{context}",
            _SYSTEM,
            max_tokens=1500,
        )
        result = extract_json(raw)
        return {"did_you_know_facts": result.get("facts", [])}
    except Exception as e:
        return {"did_you_know_facts": [], "error": f"Did-You-Know error: {e}"}
