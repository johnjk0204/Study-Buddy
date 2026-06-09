"""Article writer agent — produces an engaging school-magazine-style article.

Runs immediately after the analyzer (4th call in the pipeline) so it fires
while the connection pool is still fresh, well before any rate-limit pressure
builds up from the remaining agents.
"""
from utils.llm import call_claude
from graph.state import PassageState


_SYSTEM = """You are a writer for a school science and discovery magazine loved by students aged 10-18.
Your articles are known for being engaging, funny, and making complex topics feel exciting.

Write a 550-700 word article based on the provided content that:
- Opens with a hook question or surprising fact that grabs attention immediately
- Uses short paragraphs, conversational tone, active voice
- Includes 2 "Fun Fact!" callout boxes (bold text) embedded naturally
- Uses real-world analogies students relate to (sports, food, video games, social media — as appropriate)
- Has 3-4 subheadings (use ##) to break up sections
- Ends with a single thought-provoking question that invites the student to think further

Format:
# [CATCHY TITLE IN CAPS]

[Opening hook paragraph]

## [Section 1 heading]
[content]

**Fun Fact!** [surprising fact]

## [Section 2 heading]
[content]

## [Section 3 heading]
[content]

**Fun Fact!** [another surprising fact]

## [Conclusion heading]
[Closing paragraph ending with one open question]"""


def _template_article(state: PassageState) -> dict:
    """Fallback: build a structured article from already-available state data."""
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    grade    = state.get("grade_level") or "Grade 6-12"
    concepts = state.get("key_concepts") or []
    summary  = state.get("brief_summary") or ""

    title = f"{topic}: A Complete Guide"
    lines = [f"# {title.upper()}", ""]

    if summary:
        lines += [summary, ""]

    lines += [f"## What Is {topic}?", ""]
    if concepts:
        lines += [
            f"In {subject}, {topic} revolves around these essential ideas: "
            f"{', '.join(concepts[:5])}.",
            "",
        ]

    lines += [
        f"## Why It Matters",
        "",
        f"**Fun Fact!** {topic} is one of the core topics studied at {grade} level "
        f"precisely because it connects to so many real-world situations.",
        "",
        f"Whether you're encountering {topic} for the first time or deepening your "
        f"understanding, the concepts above form a strong foundation for everything "
        f"that follows in {subject}.",
        "",
        f"## Key Ideas to Keep in Mind",
        "",
        f"The passage highlights concepts that show up repeatedly across {subject}. "
        f"Pay close attention to how each idea connects to the others — that network "
        f"of connections is what makes learning stick.",
        "",
        f"**Fun Fact!** Research shows that connecting new information to things you "
        f"already know makes it up to 70 % easier to recall during exams.",
        "",
        f"## Final Thoughts",
        "",
        f"Understanding {topic} is a gateway to deeper knowledge in {subject}. "
        f"Review the key concepts, quiz yourself on the facts, and ask: "
        f"how does {topic} show up in your daily life?",
    ]

    return {"article_title": title, "article_content": "\n".join(lines)}


async def async_article_agent(state: PassageState) -> dict:
    """Async Summary Agent — runs in parallel after Topic Extractor."""
    from utils.llm import acall_claude
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )
    try:
        article = await acall_claude(
            f"Write an engaging school-magazine article:\n\n{context}",
            _SYSTEM,
            max_tokens=2048,
        )
        lines = article.strip().splitlines()
        title = lines[0].lstrip("# ").strip() if lines else state.get("topic", "Article")
        return {"article_title": title, "article_content": article}
    except Exception:
        return _template_article(state)


def article_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Grade Level: {state.get('grade_level', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )

    try:
        article = call_claude(
            f"Write an engaging school-magazine article:\n\n{context}",
            _SYSTEM,
            max_tokens=2048,
        )
        lines = article.strip().splitlines()
        title = lines[0].lstrip("# ").strip() if lines else state.get("topic", "Article")
        return {"article_title": title, "article_content": article}
    except Exception:
        return _template_article(state)
