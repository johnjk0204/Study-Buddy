"""Quiz Agent — adapts difficulty and language to the requested grade."""
from utils.llm import acall_claude, call_claude, extract_json, MODEL_BEST
from graph.state import PassageState


_YOUNG_SYSTEM = """You are making a fun quiz for children aged 5-7.
Create 5 simple multiple-choice questions with very easy language.

CRITICAL: Return ONLY valid JSON — no explanation, no markdown.

{
  "questions": [
    {
      "question": "Simple fun question in max 10 easy words?",
      "options": ["Short answer 1", "Short answer 2", "Short answer 3", "Short answer 4"],
      "correct_answer": "Exact text of the correct option",
      "explanation": "Great! [One simple sentence explaining why, starting with 'Great!' or 'Yes!']"
    }
  ]
}

Rules:
- options: plain text, NO letter prefixes like "A."
- Correct_answer must EXACTLY match one of the four options
- Questions should be fun: "What colour is...?", "Which animal...?", "How many...?"
- Use comparisons kids know: "as big as a bus", "like your school bag"
- Wrong options should be simple and obviously different (not tricky)"""

_MIDDLE_SYSTEM = """You are an educational quiz designer for students aged 8-11.
Create 5 multiple-choice questions — mix of fun and challenging.

Return ONLY valid JSON:
{
  "questions": [
    {
      "question": "Clear question about the topic",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Exact text of correct option",
      "explanation": "1-2 sentences explaining why this is correct"
    }
  ]
}

Rules:
- options: plain text, NO letter prefixes like "A."
- correct_answer must EXACTLY match one option
- Mix: 2 recall, 2 comprehension, 1 fun application question
- Keep language simple and clear
- Wrong options should be plausible but clearly wrong on reflection"""

_SENIOR_SYSTEM = """You are an expert quiz designer for students aged 12-18.
Create 5 high-quality multiple-choice questions testing genuine understanding.

Return ONLY valid JSON:
{
  "questions": [
    {
      "question": "Specific question directly answerable from the passage",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Exact text of the correct option",
      "explanation": "1-2 sentences: why correct, and what makes wrong options incorrect"
    }
  ]
}

Rules:
- options: plain text, NO letter prefixes like "A."
- correct_answer must EXACTLY match one option
- Vary difficulty: 2 recall, 2 comprehension, 1 application
- Wrong options must be plausible — not obviously silly
- Each question tests a different concept"""


def _pick_system(state) -> str:
    g = (state.get("requested_grade") or "").lower()
    if "1" in g or "2" in g:
        return _YOUNG_SYSTEM
    if "3" in g or "4" in g or "5" in g:
        return _MIDDLE_SYSTEM
    return _SENIOR_SYSTEM


def _fallback_quiz(state: PassageState) -> dict:
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    concepts = state.get("key_concepts") or []
    g = (state.get("requested_grade") or "").lower()
    questions = []
    for c in concepts[:5]:
        opt_a = f"Something important about {topic}" if ("1" in g or "2" in g) else \
                f"A key idea in {subject} related to {topic}"
        questions.append({
            "question": f"What is '{c}'?" if ("1" in g or "2" in g) else
                        f"Which best describes '{c}' in the context of {topic}?",
            "options": [opt_a, "Something from a different subject",
                        "Something we haven't learned yet", "Something made up"],
            "correct_answer": opt_a,
            "explanation": f"Yes! '{c}' is part of what we learned about {topic}.",
        })
    while len(questions) < 3:
        opt_a = subject
        questions.append({
            "question": f"What subject is this passage about?",
            "options": [opt_a, "Art", "Music", "Physical Education"],
            "correct_answer": opt_a,
            "explanation": f"This passage is about {subject}.",
        })
    return {"quiz_questions": questions[:5]}


async def async_quiz_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = await acall_claude(
            f"Generate 5 quiz questions for:\n\n{context}",
            _pick_system(state), max_tokens=1600, model=MODEL_BEST,
        )
        result = extract_json(raw)
        return {"quiz_questions": result.get("questions", [])}
    except Exception:
        return _fallback_quiz(state)


def quiz_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = call_claude(
            f"Generate 5 quiz questions for:\n\n{context}",
            _pick_system(state), max_tokens=1600, model=MODEL_BEST,
        )
        result = extract_json(raw)
        return {"quiz_questions": result.get("questions", [])}
    except Exception:
        return _fallback_quiz(state)
