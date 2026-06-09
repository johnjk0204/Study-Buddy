"""Smart analyzer — compresses the passage AND extracts metadata in one API call.

Falls back to _local_analyze() when the Groq API is unavailable so that topic,
subject, grade level, and key concepts are always populated from the passage text.
"""
import re
from collections import Counter
from utils.llm import call_claude, extract_json
from graph.state import PassageState


_SYSTEM = """You are an educational content analyst and text processor.

Perform two tasks in one response:
1. Compress the passage to ~50 % of its length, preserving every key concept, fact, and relationship. Remove filler and redundant phrases only.
2. Analyze the compressed content for educational metadata.

Return ONLY this JSON — no markdown, no extra text:
{
  "compressed_passage": "your compressed version of the input passage",
  "topic": "main topic in 3-5 words",
  "subject": "school subject (Science / History / Mathematics / English / Geography / Biology / etc.)",
  "grade_level": "estimated grade level (e.g. Grade 3-5 / Grade 6-8 / Grade 9-12)",
  "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
  "brief_summary": "2-3 sentence plain-language summary suitable for students"
}"""


# ── Local heuristic analyzer ───────────────────────────────────────────────────

_SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "English":     ["phrase", "grammar", "vocabulary", "sentence", "word", "language",
                    "meaning", "usage", "idiom", "metaphor", "tense", "clause", "punctuation"],
    "Biology":     ["cell", "organism", "dna", "protein", "photosynthesis", "evolution",
                    "gene", "species", "tissue", "organ", "bacteria", "virus"],
    "Chemistry":   ["atom", "molecule", "reaction", "element", "compound", "acid",
                    "base", "electron", "bond", "periodic", "oxidation"],
    "Physics":     ["force", "energy", "motion", "velocity", "mass", "gravity",
                    "wave", "electric", "magnetic", "quantum", "acceleration"],
    "Mathematics": ["equation", "function", "graph", "theorem", "proof", "angle",
                    "area", "volume", "integer", "fraction", "algebra", "calculus"],
    "History":     ["war", "century", "empire", "revolution", "king", "queen",
                    "battle", "dynasty", "civilization", "independence", "treaty"],
    "Geography":   ["country", "climate", "continent", "river", "mountain", "ocean",
                    "population", "region", "longitude", "latitude", "ecosystem"],
    "Economics":   ["market", "demand", "supply", "price", "trade", "inflation",
                    "gdp", "currency", "economy", "resource", "investment"],
    "Computer Science": ["algorithm", "code", "program", "data", "variable", "loop",
                         "function", "array", "network", "software", "hardware"],
    "Science":     ["experiment", "hypothesis", "observation", "evidence", "theory",
                    "lab", "microscope", "particle", "nucleus", "solar"],
}

_STOPWORDS = {
    "that", "this", "with", "have", "from", "they", "been", "were", "will",
    "would", "could", "should", "when", "what", "which", "about", "just",
    "some", "more", "into", "than", "also", "your", "their", "there", "here",
    "these", "those", "each", "such", "very", "much", "many", "most", "even",
    "only", "both", "through", "during", "before", "after", "above", "below",
    "then", "once", "while", "well", "like", "make", "know", "take", "come",
    "good", "same", "does", "time", "year", "long", "down", "never", "always",
    "let", "alone", "sentence", "sentences",  # suppress function-word false positives
}


def _local_analyze(passage: str) -> dict:
    """
    Heuristic topic / subject / grade-level extraction.
    Used when the Groq API is completely unavailable.
    """
    lower = passage.lower()

    # ── Subject ──────────────────────────────────────────────────────────────
    scores = {s: sum(1 for kw in kws if kw in lower) for s, kws in _SUBJECT_KEYWORDS.items()}
    best_score = max(scores.values())
    subject = max(scores, key=scores.get) if best_score > 0 else "General"

    # ── Topic ─────────────────────────────────────────────────────────────────
    # 1. Prefer quoted or italicised phrases  e.g. 'let alone'  "photosynthesis"
    quoted = re.findall(
        r"['‘’“”\"]([^'‘’“”\"]{3,40})['‘’“”\"]",
        passage,
    )
    # 2. Capitalised multi-word sequences  (e.g. Newton's First Law)
    caps = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", passage)
    # 3. Most-frequent content word
    all_words = re.findall(r"\b[a-zA-Z]{4,}\b", passage)
    content_words = [w.lower() for w in all_words if w.lower() not in _STOPWORDS]
    freq = Counter(content_words)
    top_words = [w for w, _ in freq.most_common(5)]

    if quoted:
        topic = quoted[0].strip().title()
    elif caps:
        topic = Counter(caps).most_common(1)[0][0]
    elif top_words:
        topic = top_words[0].title()
    else:
        topic = "This Topic"

    # ── Grade level (from average sentence length) ───────────────────────────
    sents = [s.strip() for s in re.split(r"[.!?]+", passage) if s.strip()]
    avg_len = sum(len(s.split()) for s in sents) / max(len(sents), 1)
    if avg_len < 8:
        grade = "Grade 1-4"
    elif avg_len < 12:
        grade = "Grade 5-7"
    elif avg_len < 18:
        grade = "Grade 8-10"
    else:
        grade = "Grade 10-12"

    # ── Key concepts (most frequent meaningful words) ─────────────────────────
    key_concepts = [w for w, _ in freq.most_common(10)
                    if w not in _STOPWORDS and len(w) > 3][:6]

    # ── Brief summary (first two substantive sentences) ───────────────────────
    good_sents = [s.strip() for s in sents if len(s.split()) > 7][:2]
    brief_summary = " ".join(good_sents) if good_sents else passage[:250]

    # ── Light compression (first 60 % of words) ───────────────────────────────
    words = passage.split()
    cutoff = max(60, int(len(words) * 0.6))
    compressed = " ".join(words[:cutoff]) if len(words) > cutoff else passage

    return {
        "compressed_passage": compressed,
        "topic":        topic,
        "subject":      subject,
        "grade_level":  grade,
        "key_concepts": key_concepts,
        "brief_summary": brief_summary,
    }


# ── Agents ────────────────────────────────────────────────────────────────────

async def async_analyzer_agent(state: PassageState) -> dict:
    """Async version — used by the parallel LangGraph graph (Topic Extractor node)."""
    from utils.llm import acall_claude
    try:
        raw = await acall_claude(
            f"Compress and analyze this educational passage:\n\n{state['passage']}",
            _SYSTEM,
            max_tokens=1024,
        )
        result = extract_json(raw)
        passage = state["passage"]
        compressed = result.get("compressed_passage") or passage
        if len(compressed.split()) >= len(passage.split()):
            compressed = passage
        return {
            "compressed_passage": compressed,
            "topic":         result.get("topic", "Unknown Topic"),
            "subject":       result.get("subject", "General"),
            "grade_level":   result.get("grade_level", "Grade 6-12"),
            "key_concepts":  result.get("key_concepts", []),
            "brief_summary": result.get("brief_summary", ""),
        }
    except Exception as exc:
        local = _local_analyze(state["passage"])
        local["error"] = f"Analyzer used offline mode ({type(exc).__name__})"
        return local


def analyzer_agent(state: PassageState) -> dict:
    try:
        raw = call_claude(
            f"Compress and analyze this educational passage:\n\n{state['passage']}",
            _SYSTEM,
            max_tokens=1024,
        )
        result = extract_json(raw)
        passage = state["passage"]
        compressed = result.get("compressed_passage") or passage
        # Safety: never accept a "compressed" version longer than the original
        if len(compressed.split()) >= len(passage.split()):
            compressed = passage
        return {
            "compressed_passage": compressed,
            "topic":        result.get("topic", "Unknown Topic"),
            "subject":      result.get("subject", "General"),
            "grade_level":  result.get("grade_level", "Grade 6-12"),
            "key_concepts": result.get("key_concepts", []),
            "brief_summary":result.get("brief_summary", ""),
        }
    except Exception as exc:
        local = _local_analyze(state["passage"])
        local["error"] = f"Analyzer used offline mode ({type(exc).__name__})"
        return local
