"""Visuals agent — suggests relevant images and diagrams with search keywords."""
from utils.llm import call_claude, extract_json
from graph.state import PassageState


_SYSTEM = """You are an educational visual content curator for school students.
Suggest visual aids (photos, diagrams, charts, maps, illustrations) that help explain the passage.

For each visual:
- Describe exactly what it should show
- Explain how it connects to the lesson
- Give 3 image search keywords students can use on Google Images or Unsplash

Respond with JSON only — no extra text:
{
  "visuals": [
    {
      "title": "short descriptive title",
      "type": "photo | diagram | infographic | chart | map | illustration",
      "description": "detailed description of what the image shows",
      "how_it_helps": "one sentence: how this visual aids understanding",
      "search_terms": ["keyword1", "keyword2", "keyword3"],
      "emoji": "one relevant emoji"
    }
  ]
}

Generate exactly 5 visuals."""


_VISUAL_MAP = {
    "english":     [("Usage Chart","chart","📊"),("Mind Map","infographic","📝"),("Example Table","diagram","📋"),("Word Web","infographic","🕸️")],
    "science":     [("Diagram","diagram","🔬"),("Data Chart","chart","📈"),("Infographic","infographic","🧪"),("Illustration","illustration","🌱")],
    "biology":     [("Cell Diagram","diagram","🧬"),("Life Cycle","illustration","🔄"),("Comparison","chart","📊"),("Ecosystem Map","infographic","🌿")],
    "chemistry":   [("Atom Diagram","diagram","⚛️"),("Periodic Table","infographic","🧪"),("Reaction Flow","diagram","🔁"),("Molecule Model","illustration","🔮")],
    "physics":     [("Force Diagram","diagram","⚡"),("Energy Chart","chart","📈"),("Wave Diagram","diagram","〰️"),("Infographic","infographic","🚀")],
    "mathematics": [("Function Graph","chart","📐"),("Number Line","diagram","🔢"),("Proof Chart","diagram","📊"),("Formula Sheet","infographic","✏️")],
    "history":     [("Timeline","infographic","📜"),("Map","map","🗺️"),("Cause & Effect","diagram","⚖️"),("Portrait","photo","👑")],
    "geography":   [("World Map","map","🌍"),("Climate Chart","chart","🌡️"),("Infographic","infographic","🏔️"),("Satellite Photo","photo","🛰️")],
}


def _fallback_visuals(state: PassageState) -> dict:
    topic   = state.get("topic") or "This Topic"
    subject = state.get("subject") or "General"
    base = _VISUAL_MAP.get(subject.lower(), [
        ("Overview Diagram","diagram","🖼️"),("Key Concepts Infographic","infographic","📊"),
        ("Summary Chart","chart","📋"),("Illustrated Guide","illustration","✏️"),
    ])
    visuals = [
        {"title": f"{vt} — {topic}", "type": vtype, "emoji": em,
         "description": f"A {vtype} capturing the key ideas of '{topic}' in {subject}.",
         "how_it_helps": f"Offers a visual entry point into {topic} more vivid than prose alone.",
         "search_terms": [f"{topic} {vtype}", f"{subject} {topic}", f"{topic} explained visual"]}
        for vt, vtype, em in base[:4]
    ]
    return {"visual_descriptions": visuals}


def visuals_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )
    try:
        raw = call_claude(
            f"Suggest educational visuals for this content:\n\n{context}",
            _SYSTEM,
            max_tokens=2000,
        )
        result = extract_json(raw)
        return {"visual_descriptions": result.get("visuals", [])}
    except Exception:
        return _fallback_visuals(state)


async def async_visuals_agent(state: PassageState) -> dict:
    """Async Image Agent — runs in parallel after Topic Extractor."""
    from utils.llm import acall_claude
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = await acall_claude(
            f"Suggest educational visuals for this content:\n\n{context}",
            _SYSTEM,
            max_tokens=2000,
        )
        result = extract_json(raw)
        return {"visual_descriptions": result.get("visuals", [])}
    except Exception:
        return _fallback_visuals(state)
