"""Combined content agent — generates facts, visuals, AND takeaways in one call.

Replaces the three separate did_you_know / visuals / takeaways agents so the
pipeline makes 4 API calls instead of 7.  If the API call fails, _fallback()
builds usable content from already-available state data — no API call needed.
"""
import re
from utils.llm import call_claude, extract_json
from graph.state import PassageState


_SYSTEM = """You are an enthusiastic educational content creator for school students aged 10-18.
Given the passage metadata, produce ALL three content types in a single JSON response.

Return ONLY valid JSON — no explanation, no markdown fences:
{
  "facts": [
    {
      "fact": "Did you know that...",
      "emoji": "one relevant emoji",
      "wow_factor": "one sentence explaining why this is mind-blowing"
    }
  ],
  "visuals": [
    {
      "title": "short descriptive title",
      "type": "photo | diagram | infographic | chart | map | illustration",
      "description": "what the image shows",
      "how_it_helps": "how this visual aids understanding",
      "search_terms": ["keyword1", "keyword2", "keyword3"],
      "emoji": "one relevant emoji"
    }
  ],
  "takeaways": [
    {
      "point": "the key learning point in plain language",
      "why_important": "one sentence of real-world relevance",
      "emoji": "one relevant emoji"
    }
  ]
}

Generate exactly: 5 facts, 4 visuals, 5 takeaways."""


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
            _SYSTEM,
            max_tokens=1800,
        )
        result = extract_json(raw)
        return {
            "did_you_know_facts":  result.get("facts",     []),
            "visual_descriptions": result.get("visuals",   []),
            "key_takeaways":       result.get("takeaways", []),
        }
    except Exception:
        try:
            result = _fallback(state)
            # Fallback succeeded — content is usable, clear any lingering error
            result["error"] = None
            return result
        except Exception as fb_exc:
            return {
                "did_you_know_facts": [],
                "visual_descriptions": [],
                "key_takeaways": [],
                "error": f"Content could not be generated (template also failed: {fb_exc})",
            }


def _fallback(state: PassageState) -> dict:
    """Build facts, visuals, and takeaways from passage text — no API call."""
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    grade    = state.get("grade_level") or "Grade 6-12"
    concepts = state.get("key_concepts") or []
    passage  = state.get("compressed_passage") or state.get("passage") or ""
    summary  = state.get("brief_summary") or ""

    # ── Facts ─────────────────────────────────────────────────────────────────
    # Priority: (1) definition sentences  (2) example sentences  (3) any long sentence
    all_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", passage) if len(s.split()) > 6]

    def _is_definition(s):
        return bool(re.search(r"\b(means|meaning|refers to|is called|is defined|is a|are a|stands for)\b", s, re.I))

    def _is_example(s):
        return bool(re.search(r"\b(for example|for instance|such as|e\.g\.|i\.e\.|like)\b", s, re.I))

    defs     = [s for s in all_sents if _is_definition(s)]
    examples = [s for s in all_sents if _is_example(s) and s not in defs]
    others   = [s for s in all_sents if s not in defs and s not in examples]

    # Assemble pool — cap each category to avoid repetition
    fact_pool = (defs[:2] + examples[:2] + others)[:5]
    while len(fact_pool) < 5:
        fact_pool.append(
            f"The concept of '{topic}' is a fascinating part of {subject} "
            f"that rewards careful study and reflection."
        )

    _wow_templates = [
        f"A deeper understanding of {topic} illuminates much of what we take for granted in {subject}.",
        f"This concept connects to countless real-world situations you encounter every day.",
        f"Those who truly grasp {topic} find the broader landscape of {subject} far clearer.",
        f"This is one of the quiet cornerstones of {subject} — easy to overlook, impossible to forget.",
        f"Knowing this opens a door to richer conversations and sharper critical thinking.",
    ]
    facts = [
        {
            "fact": (
                s if s.lower().startswith("did you")
                else f"Did you know? {s.rstrip('.')}."
            ),
            "emoji": "💡",
            "wow_factor": _wow_templates[i % len(_wow_templates)],
        }
        for i, s in enumerate(fact_pool[:5])
    ]

    # ── Visuals ───────────────────────────────────────────────────────────────
    _visual_map = {
        "english":          [("Usage Chart",   "chart",       "📊"), ("Mind Map",      "infographic", "📝"),
                             ("Example Table", "diagram",     "📋"), ("Word Web",      "infographic", "🕸️")],
        "science":          [("Diagram",       "diagram",     "🔬"), ("Data Chart",    "chart",       "📈"),
                             ("Infographic",   "infographic", "🧪"), ("Illustration",  "illustration","🌱")],
        "biology":          [("Cell Diagram",  "diagram",     "🧬"), ("Life Cycle",    "illustration","🔄"),
                             ("Comparison",    "chart",       "📊"), ("Ecosystem Map", "infographic", "🌿")],
        "chemistry":        [("Atom Diagram",  "diagram",     "⚛️"), ("Periodic Table","infographic", "🧪"),
                             ("Reaction Flow", "diagram",     "🔁"), ("Molecule Model","illustration","🔮")],
        "physics":          [("Force Diagram", "diagram",     "⚡"), ("Energy Chart",  "chart",       "📈"),
                             ("Wave Diagram",  "diagram",     "〰️"), ("Infographic",   "infographic", "🚀")],
        "mathematics":      [("Function Graph","chart",       "📐"), ("Number Line",  "diagram",     "🔢"),
                             ("Proof Chart",   "diagram",     "📊"), ("Formula Sheet", "infographic", "✏️")],
        "history":          [("Timeline",      "infographic", "📜"), ("Map",           "map",         "🗺️"),
                             ("Cause & Effect","diagram",     "⚖️"), ("Portrait",      "photo",       "👑")],
        "geography":        [("World Map",     "map",         "🌍"), ("Climate Chart", "chart",       "🌡️"),
                             ("Infographic",   "infographic", "🏔️"), ("Satellite Photo","photo",      "🛰️")],
        "economics":        [("Supply Chart",  "chart",       "📈"), ("Flow Diagram",  "diagram",     "💹"),
                             ("Infographic",   "infographic", "💰"), ("Bar Graph",     "chart",       "📊")],
        "computer science": [("Flowchart",     "diagram",     "💻"), ("Architecture",  "diagram",     "🖧"),
                             ("Pseudocode",    "illustration","📋"), ("Data Structure","diagram",     "🌳")],
    }
    base_visuals = _visual_map.get(
        subject.lower(),
        [("Overview Diagram", "diagram", "🖼️"), ("Key Concepts Infographic", "infographic", "📊"),
         ("Summary Chart",    "chart",   "📋"), ("Illustrated Guide",        "illustration","✏️")],
    )
    # Add one concept-specific visual if we have concepts
    if concepts:
        base_visuals = list(base_visuals) + [(f"{concepts[0].title()} Illustration", "illustration", "💡")]

    visuals = [
        {
            "title": f"{vt} — {topic}",
            "type": vtype,
            "description": (
                f"A {vtype} capturing the essential ideas of '{topic}' "
                f"in the context of {subject}."
            ),
            "how_it_helps": (
                f"Offers a visual entry point into {topic} that is often "
                f"more vivid and memorable than prose alone."
            ),
            "search_terms": [f"{topic} {vtype}", f"{subject} {topic}", f"{topic} explained visual"],
            "emoji": em,
        }
        for vt, vtype, em in base_visuals[:4]
    ]

    # ── Takeaways ─────────────────────────────────────────────────────────────
    concept_takeaways = [
        {
            "point": f"Understand what '{c}' means and how it operates within {topic}.",
            "why_important": f"'{c}' is one of the quiet pillars of {subject} — grasp it and much else becomes clear.",
            "emoji": "✅",
        }
        for c in concepts[:4]
    ]
    takeaways = concept_takeaways + [
        {
            "point": f"Connect {topic} to real-world examples in your daily life.",
            "why_important": "Real-world connections make abstract ideas stick far longer.",
            "emoji": "🌟",
        }
    ]

    return {
        "did_you_know_facts":  facts[:5],
        "visual_descriptions": visuals[:4],
        "key_takeaways":       takeaways[:5],
    }
