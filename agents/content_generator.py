"""Sync content agent (Streamlit path) — facts + visuals + takeaways in one 70b call."""
from utils.llm import call_claude, extract_json, MODEL_BEST
from graph.state import PassageState


_SYSTEM = """You are an expert educational content creator for students aged 10-18.
Generate all three content types in a SINGLE JSON response. Return ONLY valid JSON.

{
  "facts": [
    {
      "fact": "Did you know that [specific fact with a real number, name, date, or size comparison]?",
      "emoji": "relevant emoji",
      "wow_factor": "One sentence: why this is genuinely surprising or hard to believe"
    }
  ],
  "visuals": [
    {
      "title": "Descriptive title specific to this topic",
      "type": "diagram | infographic | chart | map | illustration | timeline",
      "description": "Exactly what this visual shows — specific to the topic, not generic",
      "how_it_helps": "How this visual makes the concept easier to understand",
      "search_terms": ["specific keyword 1", "specific keyword 2", "specific keyword 3"],
      "emoji": "relevant emoji"
    }
  ],
  "takeaways": [
    {
      "point": "Clear, actionable learning point starting with a verb",
      "why_important": "Real-world connection — a job, daily life, or future study link",
      "emoji": "relevant emoji"
    }
  ]
}

Generate exactly: 5 facts, 4 visuals, 5 takeaways.
Facts MUST include specific numbers, names, or comparisons — not vague statements.
Visuals MUST be specific to the exact topic, not generic "diagram" descriptions."""


def content_generator_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Grade Level: {state.get('grade_level', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )
    try:
        raw = call_claude(
            f"Generate educational facts, visuals, and takeaways for:\n\n{context}",
            _SYSTEM, max_tokens=2200, model=MODEL_BEST,
        )
        result = extract_json(raw)
        return {
            "did_you_know_facts":  result.get("facts",     []),
            "visual_descriptions": result.get("visuals",   []),
            "key_takeaways":       result.get("takeaways", []),
        }
    except Exception:
        topic    = state.get("topic") or "This Topic"
        subject  = state.get("subject") or "General"
        concepts = state.get("key_concepts") or []
        verbs    = ["Understand", "Remember", "Explain", "Connect", "Apply"]
        return {
            "did_you_know_facts": [
                {"fact": f"Did you know that {topic} is studied across {subject} curricula worldwide?",
                 "emoji": "💡", "wow_factor": "It connects to countless real-world applications."}
            ],
            "visual_descriptions": [
                {"title": f"{topic} Overview", "type": "infographic", "emoji": "📊",
                 "description": f"Key ideas and relationships in {topic}",
                 "how_it_helps": "Provides a visual summary of the whole topic at once",
                 "search_terms": [topic, subject, f"{topic} explained"]}
            ],
            "key_takeaways": [
                {"point": f"{verbs[i % len(verbs)]} the concept of '{c}'.",
                 "why_important": f"Used in {subject} and real-world applications daily.",
                 "emoji": "✅"}
                for i, c in enumerate(concepts[:5])
            ],
        }
