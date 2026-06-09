"""Analyzer — compresses the passage AND extracts metadata in one fast API call."""
import re
from collections import Counter
from utils.llm import acall_claude, call_claude, extract_json, MODEL_FAST
from graph.state import PassageState


_SYSTEM = """You are an educational content analyst.

Perform TWO tasks and return only valid JSON — no markdown, no extra text:
1. Compress the passage to ~50% of its length, keeping every key concept, fact, name, date, and number.
2. Extract educational metadata from the compressed content.

{
  "compressed_passage": "compressed version here",
  "topic": "main topic in 3-6 words",
  "subject": "Biology | Chemistry | Physics | Mathematics | History | Geography | English | Science | Economics | Computer Science | General",
  "grade_level": "Grade 3-5 | Grade 6-8 | Grade 9-12",
  "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
  "brief_summary": "2-3 sentence plain-language summary that excites a student about this topic"
}"""


_SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "English":          ["phrase", "grammar", "vocabulary", "sentence", "word", "language", "metaphor", "tense"],
    "Biology":          ["cell", "organism", "dna", "protein", "photosynthesis", "evolution", "gene", "species"],
    "Chemistry":        ["atom", "molecule", "reaction", "element", "compound", "acid", "electron", "bond"],
    "Physics":          ["force", "energy", "motion", "velocity", "mass", "gravity", "wave", "electric"],
    "Mathematics":      ["equation", "function", "theorem", "proof", "angle", "area", "volume", "algebra"],
    "History":          ["war", "century", "empire", "revolution", "battle", "civilization", "independence", "treaty"],
    "Geography":        ["country", "climate", "continent", "river", "mountain", "ocean", "population", "ecosystem"],
    "Economics":        ["market", "demand", "supply", "price", "trade", "inflation", "gdp", "currency"],
    "Computer Science": ["algorithm", "code", "program", "data", "variable", "loop", "network", "software"],
    "Science":          ["experiment", "hypothesis", "observation", "evidence", "theory", "nucleus", "solar"],
}

_STOPWORDS = {
    "that","this","with","have","from","they","been","were","will","would","could",
    "should","when","what","which","about","just","some","more","into","than","also",
    "your","their","there","here","these","those","each","such","very","much","many",
}


def _local_analyze(passage: str) -> dict:
    lower  = passage.lower()
    scores = {s: sum(1 for kw in kws if kw in lower) for s, kws in _SUBJECT_KEYWORDS.items()}
    best   = max(scores.values())
    subject = max(scores, key=scores.get) if best > 0 else "General"

    quoted  = re.findall(r"[\"'][^\"']{3,40}[\"']", passage)
    caps    = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", passage)
    words   = re.findall(r"\b[a-zA-Z]{4,}\b", passage)
    content = [w.lower() for w in words if w.lower() not in _STOPWORDS]
    freq    = Counter(content)
    top     = [w for w, _ in freq.most_common(5)]

    topic = quoted[0].strip().title() if quoted else \
            Counter(caps).most_common(1)[0][0] if caps else \
            top[0].title() if top else "This Topic"

    sents   = [s.strip() for s in re.split(r"[.!?]+", passage) if s.strip()]
    avg_len = sum(len(s.split()) for s in sents) / max(len(sents), 1)
    grade   = "Grade 3-5" if avg_len < 8 else "Grade 6-8" if avg_len < 15 else "Grade 9-12"

    key_concepts = [w for w, _ in freq.most_common(10) if len(w) > 3][:6]
    good_sents   = [s.strip() for s in sents if len(s.split()) > 7][:2]
    brief_summary = " ".join(good_sents) if good_sents else passage[:250]

    words_list = passage.split()
    cutoff     = max(60, int(len(words_list) * 0.6))
    compressed = " ".join(words_list[:cutoff]) if len(words_list) > cutoff else passage

    return {
        "compressed_passage": compressed,
        "topic": topic, "subject": subject, "grade_level": grade,
        "key_concepts": key_concepts, "brief_summary": brief_summary,
    }


async def async_analyzer_agent(state: PassageState) -> dict:
    try:
        raw = await acall_claude(
            f"Compress and analyze this educational passage:\n\n{state['passage']}",
            _SYSTEM, max_tokens=1024, model=MODEL_FAST,
        )
        r = extract_json(raw)
        p = state["passage"]
        c = r.get("compressed_passage") or p
        if len(c.split()) >= len(p.split()):
            c = p
        return {"compressed_passage": c, "topic": r.get("topic", "Unknown Topic"),
                "subject": r.get("subject", "General"), "grade_level": r.get("grade_level", "Grade 6-8"),
                "key_concepts": r.get("key_concepts", []), "brief_summary": r.get("brief_summary", "")}
    except Exception as exc:
        local = _local_analyze(state["passage"])
        local["error"] = f"Analyzer used offline mode ({type(exc).__name__})"
        return local


def analyzer_agent(state: PassageState) -> dict:
    try:
        raw = call_claude(
            f"Compress and analyze this educational passage:\n\n{state['passage']}",
            _SYSTEM, max_tokens=1024, model=MODEL_FAST,
        )
        r = extract_json(raw)
        p = state["passage"]
        c = r.get("compressed_passage") or p
        if len(c.split()) >= len(p.split()):
            c = p
        return {"compressed_passage": c, "topic": r.get("topic", "Unknown Topic"),
                "subject": r.get("subject", "General"), "grade_level": r.get("grade_level", "Grade 6-8"),
                "key_concepts": r.get("key_concepts", []), "brief_summary": r.get("brief_summary", "")}
    except Exception as exc:
        local = _local_analyze(state["passage"])
        local["error"] = f"Analyzer used offline mode ({type(exc).__name__})"
        return local
