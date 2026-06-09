"""Takeaway Agent — key learning points AND surprising facts in one call.

Runs in parallel with the other agents after Topic Extractor completes.
Covers both 'Takeaway Agent' and 'Did You Know' content in the parallel graph.
"""
import re
from collections import Counter
from utils.llm import call_claude, extract_json
from graph.state import PassageState


_SYSTEM = """You are an enthusiastic teacher who loves surprising students with cool facts
and helping them remember what matters.

Produce TWO sections in one JSON response:

{
  "takeaways": [
    {
      "point": "key learning point in plain language",
      "why_important": "one sentence: real-world relevance",
      "emoji": "one relevant emoji"
    }
  ],
  "facts": [
    {
      "fact": "Did you know that...",
      "emoji": "one relevant emoji",
      "wow_factor": "one sentence explaining why this is mind-blowing"
    }
  ]
}

Generate exactly: 5 takeaways, 5 facts.
Facts must start with "Did you know that…" and be surprising but accurate."""

_STOPWORDS = {
    "that","this","with","have","from","they","been","were","will","would","could",
    "should","when","what","which","about","just","some","more","into","than","also",
}


def _fallback_takeaways(state: PassageState) -> dict:
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    concepts = state.get("key_concepts") or []
    passage  = state.get("compressed_passage") or state.get("passage") or ""

    takeaways = [
        {"point": f"Understand what '{c}' means and how it operates within {topic}.",
         "why_important": f"'{c}' is one of the quiet pillars of {subject} — grasp it and much else becomes clear.",
         "emoji": "✅"}
        for c in concepts[:4]
    ] + [{"point": f"Connect {topic} to real-world examples in your daily life.",
          "why_important": "Real-world connections make abstract ideas stick far longer.",
          "emoji": "🌟"}]

    all_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", passage) if len(s.split()) > 7]
    wow_templates = [
        f"A deeper understanding of {topic} illuminates much of what we take for granted in {subject}.",
        f"This concept connects to countless real-world situations you encounter every day.",
        f"Those who truly grasp {topic} find the broader landscape of {subject} far clearer.",
        f"This is one of the quiet cornerstones of {subject} — easy to overlook, impossible to forget.",
        f"Knowing this opens a door to richer conversations and sharper critical thinking.",
    ]
    facts = [
        {"fact": f"Did you know? {s.rstrip('.')}.",
         "emoji": "💡",
         "wow_factor": wow_templates[i % len(wow_templates)]}
        for i, s in enumerate(all_sents[:5])
    ]
    while len(facts) < 5:
        facts.append({"fact": f"Did you know that '{topic}' is a fascinating area of {subject} that connects to everyday life?",
                      "emoji": "💡", "wow_factor": wow_templates[len(facts) % len(wow_templates)]})

    return {"key_takeaways": takeaways[:5], "did_you_know_facts": facts[:5]}


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
            _SYSTEM,
            max_tokens=1600,
        )
        result = extract_json(raw)
        return {
            "key_takeaways":    result.get("takeaways", []),
            "did_you_know_facts": result.get("facts", []),
        }
    except Exception:
        return _fallback_takeaways(state)


async def async_takeaways_agent(state: PassageState) -> dict:
    """Async Takeaway Agent — runs in parallel after Topic Extractor."""
    from utils.llm import acall_claude
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = await acall_claude(
            f"Generate takeaways and facts for:\n\n{context}",
            _SYSTEM,
            max_tokens=1600,
        )
        result = extract_json(raw)
        return {
            "key_takeaways":      result.get("takeaways", []),
            "did_you_know_facts": result.get("facts", []),
        }
    except Exception:
        return _fallback_takeaways(state)
