"""Study Buddy AI — Streamlit frontend."""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Study Buddy AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .hero-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 1.25rem;
        color: white;
        text-align: center;
        margin-bottom: 1.75rem;
        box-shadow: 0 8px 24px rgba(102,126,234,.35);
    }
    .hero-banner h1 { font-size: 2.4rem; margin: 0 0 .4rem; }
    .hero-banner p  { font-size: 1.1rem; margin: 0; opacity: .9; }

    .blocked-box {
        background: linear-gradient(135deg, #ff6b6b, #ee0979);
        color: white;
        padding: 2rem;
        border-radius: 1.25rem;
        text-align: center;
        box-shadow: 0 6px 20px rgba(238,9,121,.3);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render_hero():
    st.markdown(
        """
        <div class="hero-banner">
            <h1>📚 Study Buddy AI</h1>
            <p>Paste any educational passage and watch it transform into fun, easy-to-understand content!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _render_hero()

    if not os.getenv("GROQ_API_KEY"):
        st.error(
            "⚠️ **GROQ_API_KEY not found.**\n\n"
            "Create a `.env` file in the project folder and add:\n"
            "```\nGROQ_API_KEY=your_key_here\n```"
        )
        return

    # ── Gutenberg book browser ─────────────────────────────────────────────
    from utils.gutenberg_api import get_subjects, get_books, get_book_passage

    if "passage_text" not in st.session_state:
        st.session_state.passage_text = ""

    with st.expander("📖 Browse Classic Books (Project Gutenberg)", expanded=False):
        try:
            @st.cache_data(show_spinner=False)
            def _subjects():
                return get_subjects()

            @st.cache_data(show_spinner=False)
            def _books(subject: str):
                return get_books(subject=subject)

            subjects = _subjects()
            if not subjects:
                st.warning("Could not load subjects — check your network connection.")
            else:
                gcol1, gcol2 = st.columns(2)
                with gcol1:
                    chosen_subject = st.selectbox(
                        "Subject", ["— choose a subject —"] + subjects, key="gut_subject"
                    )
                book_list = []
                if chosen_subject and chosen_subject != "— choose a subject —":
                    with st.spinner("Loading books…"):
                        book_list = _books(chosen_subject)

                if book_list:
                    book_map = {
                        f"{b.get('title', 'Unknown')} — {b.get('author', b.get('authors', 'Unknown'))}": b
                        for b in book_list
                    }
                    with gcol2:
                        chosen_label = st.selectbox("Book", list(book_map.keys()), key="gut_book")
                    chosen_book = book_map[chosen_label]

                    load_col, info_col = st.columns([1, 3])
                    with load_col:
                        load_btn = st.button("Load Opening Passage", key="gut_load", use_container_width=True)
                    with info_col:
                        st.caption("Loads the first ~450 words into the passage box below.")

                    if load_btn:
                        with st.spinner("Fetching passage…"):
                            passage_fetched = get_book_passage(chosen_book, max_words=450)
                        if passage_fetched:
                            st.session_state.passage_text = passage_fetched
                            title = chosen_book.get("title", "this book")
                            st.success(f"Loaded opening passage from **{title}**")
                            st.rerun()
                        else:
                            st.warning("Could not retrieve text for this book. Try another title.")
                elif chosen_subject != "— choose a subject —":
                    st.info("No books found for this subject.")

        except Exception as gut_err:
            st.warning(f"Book browser unavailable: {gut_err}")

    # ── Input ──────────────────────────────────────────────────────────────
    st.markdown("### 📝 Paste Your Passage")
    passage = st.text_area(
        label="passage_input",
        label_visibility="collapsed",
        key="passage_text",
        height=220,
        placeholder=(
            "Paste any educational text here — a lesson, textbook paragraph, "
            "article, or transcript. Study Buddy will do the rest! 🚀"
        ),
    )

    left, right = st.columns([4, 1])
    with right:
        analyze = st.button("🚀 Analyze!", type="primary", use_container_width=True)

    if not analyze:
        return

    if not passage.strip():
        st.warning("⚠️ Please paste a passage first!")
        return

    # ── Run the LangGraph pipeline with live progress ──────────────────────
    from graph.workflow import build_graph
    from graph.state import PassageState

    graph = build_graph()

    initial_state: PassageState = {
        "passage": passage,
        "compressed_passage": "",
        "guardrail_status": "",
        "guardrail_issues": [],
        "topic": "",
        "subject": "",
        "grade_level": "",
        "key_concepts": [],
        "brief_summary": "",
        "did_you_know_facts": [],
        "visual_descriptions": [],
        "key_takeaways": [],
        "quiz_questions": [],
        "article_title": "",
        "article_content": "",
        "error": None,
    }

    final_state: dict = dict(initial_state)
    blocked = False

    step_labels = {
        "guardrail_check":   "🛡️  Checking content safety…",
        "smart_analyzer":    "⚡  Compressing & analyzing passage…",
        "article_writer":    "📰  Writing the article…",
        "content_generator": "✨  Generating facts, visuals & takeaways…",
        # async parallel graph node names
        "topic_extractor":  "⚡  Extracting topic and concepts…",
        "summary_agent":    "📰  Writing article…",
        "quiz_agent":       "❓  Generating quiz questions…",
        "image_agent":      "🖼️  Finding visual aids…",
        "takeaway_agent":   "✨  Building key takeaways…",
    }

    with st.status("⏳ Study Buddy is thinking…", expanded=True) as status:
        try:
            for event in graph.stream(initial_state):
                for node, output in event.items():
                    final_state.update(output)
                    label = step_labels.get(node, f"Running {node}…")
                    status.update(label=label)

                    if node == "guardrail_check" and output.get("guardrail_status") == "blocked":
                        status.update(label="🚫 Content blocked", state="error", expanded=True)
                        blocked = True
                        break

                if blocked:
                    break

        except Exception as exc:
            status.update(label=f"❌ Error: {exc}", state="error")
            st.error(f"**Error:** {exc}")
            st.exception(exc)
            return

        if not blocked:
            status.update(label="🎉 All done! Here's your Study Buddy breakdown.", state="complete")

    if final_state.get("error") and not blocked:
        st.warning(f"⚠️ Partial result — some agents failed: {final_state['error']}")

    # ── Display results ────────────────────────────────────────────────────
    if blocked:
        issues = final_state.get("guardrail_issues", [])
        issues_html = "".join(f"<li>{i}</li>" for i in issues)
        st.markdown(
            f"""
            <div class="blocked-box">
                <h2>⚠️ Passage Cannot Be Processed</h2>
                <p>The following issues were found:</p>
                <ul style="text-align:left;display:inline-block">{issues_html}</ul>
                <p style="margin-top:1rem">Please try a different educational passage.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Generate & display the book-style HTML report ─────────────────────
    from utils.html_renderer import render_book_html
    from utils.pdf_renderer  import render_pdf
    import streamlit.components.v1 as components

    html_report = render_book_html(final_state)
    topic_slug  = (final_state.get("topic") or "report").replace(" ", "_")

    st.markdown("---")
    dl_html_col, dl_pdf_col, _ = st.columns([1, 1, 2])

    with dl_html_col:
        st.download_button(
            label="⬇️ Download HTML",
            data=html_report.encode("utf-8"),
            file_name=f"study_buddy_{topic_slug}.html",
            mime="text/html",
            use_container_width=True,
        )

    with dl_pdf_col:
        with st.spinner("Generating PDF…"):
            try:
                pdf_bytes = render_pdf(final_state)
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"study_buddy_{topic_slug}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as pdf_err:
                st.warning(f"PDF generation failed: {pdf_err}")

    components.html(html_report, height=5200, scrolling=True)


if __name__ == "__main__":
    main()
