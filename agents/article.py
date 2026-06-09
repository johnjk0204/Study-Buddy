"""Article writer — adapts style and reading level to the requested grade."""
from utils.llm import acall_claude, call_claude, MODEL_BEST
from graph.state import PassageState


def _is_young(state) -> bool:
    g = (state.get("requested_grade") or "").lower()
    return "1" in g or "2" in g


# ── Grade 1-2: picture-book style ─────────────────────────────────────────────
_YOUNG_SYSTEM = """You are writing a picture book for children aged 5-7.
Write about the topic in 200-250 words.

Rules:
- ONLY use words a 6-year-old already knows (no long or tricky words)
- Maximum 8 words per sentence
- Use "you", "we", "let's" to speak directly to the child
- Start each short paragraph with a fun emoji
- Use exclamation points and questions to keep kids curious
- End with: "🎯 Try this! [one simple hands-on activity any child can do at home]"
- NO subheadings — just short paragraphs

Format:
# [SUPER FUN TITLE with emoji]

[4-5 short paragraphs, each starting with an emoji, max 4 sentences each]

🎯 Try this! [Simple activity]"""

# ── Grade 3-5: friendly explorer style ────────────────────────────────────────
_MIDDLE_SYSTEM = """You are a friendly science explorer writing for students aged 8-11.
Write a 350-450 word article that makes the topic feel like an adventure.

Rules:
- Use clear, simple language — no jargon
- Short snappy sentences mixed with slightly longer ones
- Include 2 "Cool Fact!" boxes (bold: **Cool Fact!**)
- Use 2-3 section headings (## style)
- End with one question that makes the student want to find out more

Format:
# [EXCITING TITLE]

[Opening — a surprising question or cool scenario]

## [Section 1]
[Content]
**Cool Fact!** [specific fact with a number]

## [Section 2]
[Content]
**Cool Fact!** [another fact]

## What Did We Learn?
[Short conclusion + one open question]"""

# ── Grade 6-12: school-magazine style ─────────────────────────────────────────
_SENIOR_SYSTEM = """You are a star writer for a school science-and-discovery magazine (ages 12-18).
Write a 600-750 word article that makes this topic impossible to put down.

- Opens with a jaw-dropping hook: shocking stat, dramatic scene, or provocative question
- Names REAL scientists, explorers, or historical figures connected to the topic
- Uses vivid analogies students recognise (gaming, sports, social media, food)
- Includes TWO "Fun Fact!" callout boxes (bold: **Fun Fact!**)
- Uses 3-4 subheadings (## style)
- Ends with ONE open question that sparks further thinking

Format:
# [CATCHY TITLE IN ALL CAPS]
[Hook paragraph]
## [Section 1]
[Content]
**Fun Fact!** [specific stat or name]
## [Section 2]
[Content]
## [Section 3]
[Content]
**Fun Fact!** [another specific fact]
## What's the Big Takeaway?
[Conclusion + open question]"""


def _pick_system(state) -> str:
    g = (state.get("requested_grade") or "").lower()
    if "1" in g or "2" in g:
        return _YOUNG_SYSTEM
    if "3" in g or "4" in g or "5" in g:
        return _MIDDLE_SYSTEM
    return _SENIOR_SYSTEM


def _template_article(state: PassageState) -> dict:
    topic    = state.get("topic") or "This Topic"
    subject  = state.get("subject") or "General"
    concepts = state.get("key_concepts") or []
    if _is_young(state):
        title   = f"Let's Learn About {topic}! 🌟"
        content = (
            f"# LET'S LEARN ABOUT {topic.upper()}! 🌟\n\n"
            f"🌈 {topic} is so cool! It is part of {subject}.\n\n"
            f"⭐ Let's find out more together!\n\n"
            f"🎯 Try this! Draw a picture of {topic} and show your family!"
        )
    else:
        title   = f"{topic}: Everything You Need to Know"
        content = (
            f"# {title.upper()}\n\n"
            f"## What Is {topic}?\n{', '.join(concepts[:5])}.\n\n"
            f"## Why It Matters\n**Fun Fact!** {topic} connects to the real world every day.\n\n"
            f"## What's the Big Takeaway?\nNow you know about {topic}. Where do you see it in your life?"
        )
    return {"article_title": title, "article_content": content}


async def async_article_agent(state: PassageState) -> dict:
    context = (
        f"Topic: {state.get('topic', '')}\n"
        f"Subject: {state.get('subject', '')}\n"
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )
    try:
        article = await acall_claude(
            f"Write an engaging article for this content:\n\n{context}",
            _pick_system(state), max_tokens=2048, model=MODEL_BEST,
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
        f"Key Concepts: {', '.join(state.get('key_concepts', []))}\n\n"
        f"Passage:\n{state.get('compressed_passage') or state['passage']}"
    )
    try:
        article = call_claude(
            f"Write an engaging article for this content:\n\n{context}",
            _pick_system(state), max_tokens=2048, model=MODEL_BEST,
        )
        lines = article.strip().splitlines()
        title = lines[0].lstrip("# ").strip() if lines else state.get("topic", "Article")
        return {"article_title": title, "article_content": article}
    except Exception:
        return _template_article(state)
