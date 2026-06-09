"""Quiz Agent — generates 5 multiple-choice questions from passage metadata.

Runs in parallel with the other agents after Topic Extractor completes.
"""
from utils.llm import call_claude, extract_json
from graph.state import PassageState


_SYSTEM = """You are an educational quiz designer for students aged 10-18.
Create 5 multiple-choice questions from the provided content.

Return ONLY valid JSON — no explanation, no markdown fences:
{
  "questions": [
    {
      "question": "Clear, specific question about the topic",
      "options": ["A. option text", "B. option text", "C. option text", "D. option text"],
      "answer": "A",
      "explanation": "One sentence explaining why this answer is correct"
    }
  ]
}

Rules:
- Questions must be answerable from the passage, not general knowledge
- Distractors (wrong options) should be plausible, not obviously wrong
- Vary difficulty: 2 recall, 2 comprehension, 1 application"""


def _fallback_quiz(state: PassageState) -> dict:
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    concepts = state.get("key_concepts") or []

    questions = []
    for i, concept in enumerate(concepts[:5]):
        questions.append({
            "question": f"Which of the following best describes '{concept}' in the context of {topic}?",
            "options": [
                f"A. It is a fundamental idea in {subject} related to {topic}.",
                f"B. It refers to an unrelated concept from a different field.",
                f"C. It only applies in advanced theoretical contexts.",
                f"D. It contradicts the core principles of {topic}.",
            ],
            "answer": "A",
            "explanation": f"'{concept}' is one of the core ideas explored in this passage about {topic}.",
        })

    while len(questions) < 3:
        questions.append({
            "question": f"What is the main subject of this passage?",
            "options": [
                f"A. {subject}",
                "B. Physical Education",
                "C. Art",
                "D. Music",
            ],
            "answer": "A",
            "explanation": f"The passage focuses on {subject} concepts related to {topic}.",
        })

    return {"quiz_questions": questions[:5]}


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
            _SYSTEM,
            max_tokens=1200,
        )
        result = extract_json(raw)
        return {"quiz_questions": result.get("questions", [])}
    except Exception:
        return _fallback_quiz(state)


async def async_quiz_agent(state: PassageState) -> dict:
    """Async Quiz Agent — runs in parallel after Topic Extractor."""
    from utils.llm import acall_claude
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state.get('passage', '')}"
    )
    try:
        raw = await acall_claude(
            f"Generate 5 quiz questions for:\n\n{context}",
            _SYSTEM,
            max_tokens=1200,
        )
        result = extract_json(raw)
        return {"quiz_questions": result.get("questions", [])}
    except Exception:
        return _fallback_quiz(state)
