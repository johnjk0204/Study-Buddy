"""
PDF generation for Study Buddy AI.

Primary  : WeasyPrint — converts our HTML report to PDF (best fidelity,
           needs GTK/Cairo on Windows: https://weasyprint.org/start/)
Fallback : fpdf2 — pure-Python, zero system deps, always works.

Install both:
    pip install weasyprint fpdf2
"""
import io
import re
import html as _html


# ── Public API ────────────────────────────────────────────────────────────────

def render_pdf(state: dict) -> bytes:
    """Return a PDF file as bytes for the given Study Buddy state dict."""
    try:
        return _via_weasyprint(state)
    except Exception:
        return _via_fpdf(state)


# ═════════════════════════════════════════════════════════════════════════════
#  PRIMARY: WeasyPrint  (HTML → PDF, preserves full design)
# ═════════════════════════════════════════════════════════════════════════════

def _via_weasyprint(state: dict) -> bytes:
    from weasyprint import HTML, CSS
    html_str = _print_html(state)
    extra = CSS(string="""
        @page { size: A4; margin: 0; }
        body  { background: #fff !important; }
        .topnav, #prog { display: none !important; }
        .page { margin-bottom: 0; box-shadow: none !important;
                border-radius: 0 !important; break-after: page;
                opacity: 1 !important; animation: none !important; }
        .closing-page { break-after: avoid; }
    """)
    return HTML(string=html_str).write_pdf(stylesheets=[extra])


def _print_html(state: dict) -> str:
    """Return a WeasyPrint-safe version of the HTML report."""
    from utils.html_renderer import render_book_html
    html = render_book_html(state)
    # Remove Google Fonts CDN (unavailable on corp network in headless mode)
    html = re.sub(r"<link[^>]+googleapis\.com[^>]*>", "", html)
    # Swap CDN font names for system-safe fallbacks
    for gf, safe in [
        ("'Poppins'",         "Arial"),
        ("'Nunito'",          "Arial"),
        ("'Playfair Display'","Georgia"),
    ]:
        html = html.replace(gf, safe)
    return html


# ═════════════════════════════════════════════════════════════════════════════
#  FALLBACK: fpdf2  (pure-Python, no system dependencies)
# ═════════════════════════════════════════════════════════════════════════════

# Color themes — (R,G,B) tuples
_THEMES = {
    "science":     ((2, 119, 189),   (245, 124, 0)),
    "biology":     ((46, 125, 50),   (249, 168, 37)),
    "chemistry":   ((106, 27, 154),  (244, 81, 30)),
    "physics":     ((21, 101, 192),  (233, 30, 99)),
    "mathematics": ((69, 39, 160),   (0, 172, 193)),
    "history":     ((109, 76, 65),   (244, 81, 30)),
    "geography":   ((0, 105, 92),    (229, 57, 53)),
    "english":     ((51, 105, 30),   (123, 31, 162)),
}
_DEF_THEME = ((78, 52, 46), (233, 30, 99))

# Page size (A4 mm)
_PW, _PH = 210, 297
_LM = _RM = 15          # left/right margin
_USABLE = _PW - _LM - _RM   # usable width


def _theme(subject: str):
    s = (subject or "").lower()
    for k, v in _THEMES.items():
        if k in s:
            return v
    return _DEF_THEME


_UNICODE_SUBS = str.maketrans({
    "—": " - ",  # em dash
    "–": " - ",  # en dash
    "‒": " - ",  # figure dash
    "’": "'",    # right single quote
    "‘": "'",    # left single quote
    "“": '"',    # left double quote
    "”": '"',    # right double quote
    "…": "...",  # ellipsis
    "•": "-",    # bullet
    "·": ".",    # middle dot  (U+00B7 — IS in latin-1 but Helvetica glyph may be missing)
    " ": " ",    # non-breaking space
    "‑": "-",    # non-breaking hyphen
    "‐": "-",    # hyphen
    "×": "x",    # multiplication sign
    "÷": "/",    # division sign
})

# Windows Arial TTF paths — supports full Unicode including emoji fallback
_WIN_FONTS = {
    "":   r"C:\Windows\Fonts\arial.ttf",
    "B":  r"C:\Windows\Fonts\arialbd.ttf",
    "I":  r"C:\Windows\Fonts\ariali.ttf",
    "BI": r"C:\Windows\Fonts\arialbi.ttf",
}


def _clean(text) -> str:
    """Strip HTML tags, normalise Unicode punctuation to ASCII, remove markdown."""
    import os
    t = _html.unescape(str(text or ""))
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"#{1,6}\s*", "", t)
    t = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", t)
    # Normalise typographic Unicode → ASCII so Helvetica can render them
    t = t.translate(_UNICODE_SUBS)
    # Drop anything remaining outside latin-1 (emoji, CJK, etc.)
    t = t.encode("latin-1", errors="ignore").decode("latin-1")
    return t.strip()


def _try_load_arial(pdf) -> bool:
    """Load Windows Arial as a Unicode font. Returns True on success."""
    import os
    if not all(os.path.exists(p) for p in _WIN_FONTS.values()):
        return False
    try:
        for style, path in _WIN_FONTS.items():
            pdf.add_font("UF", style=style, fname=path)
        return True
    except Exception:
        return False


def _lighter(rgb, factor=0.88):
    """Return a lighter tint of an RGB colour."""
    r, g, b = rgb
    return (
        int(r + (255 - r) * (1 - factor)),
        int(g + (255 - g) * (1 - factor)),
        int(b + (255 - b) * (1 - factor)),
    )


def _via_fpdf(state: dict) -> bytes:
    from fpdf import FPDF

    topic    = _clean(state.get("topic")   or "Study Topic")
    subject  = _clean(state.get("subject") or "General")
    # ──────────────────────────────────────────────────────────────────────────
    # Font selection: prefer Arial Unicode (Windows); fallback = Helvetica+ASCII
    # ──────────────────────────────────────────────────────────────────────────
    concepts = [_clean(c) for c in (state.get("key_concepts") or [])]
    summary  = _clean(state.get("brief_summary") or "")
    facts    = [f for f in (state.get("did_you_know_facts")  or []) if isinstance(f, dict)]
    tks      = [tk for tk in (state.get("key_takeaways")     or []) if isinstance(tk, dict)]
    quiz     = [q for q in (state.get("quiz_questions")      or []) if isinstance(q, dict)]
    visuals  = [v for v in (state.get("visual_descriptions") or []) if isinstance(v, dict)]
    a_title  = _clean(state.get("article_title")   or topic)
    a_body   = _clean(state.get("article_content") or "")

    pri, sec = _theme(subject)

    # ── PDF class ─────────────────────────────────────────────────────────────
    class PDF(FPDF):
        def footer(self):
            self.set_y(-12)
            self.set_font(_fn, "I", 7)
            self.set_text_color(180, 180, 180)
            self.cell(0, 6, f"Study Buddy AI  *  {topic}  *  Page {self.page_no()}",
                      align="C")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(_LM, 15, _RM)
    pdf.set_text_color(30, 30, 30)

    # Load Windows Arial for full Unicode; fall back to Helvetica + ASCII-clean
    _unicode = _try_load_arial(pdf)
    _fn = "UF" if _unicode else "Helvetica"   # font name shorthand

    def sf(style="", size=10):
        """Set current font, choosing Unicode-capable family when available."""
        pdf.set_font(_fn, style, size)

    # ── drawing helpers ────────────────────────────────────────────────────────

    def sec_bar(label: str, color=None):
        """Full-width coloured section header bar."""
        c = color or pri
        y = pdf.get_y()
        pdf.set_fill_color(*c)
        pdf.rect(_LM, y, _USABLE, 10, style="F")
        pdf.set_xy(_LM, y)
        sf("B", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(_USABLE, 10, label.upper(), align="C", ln=True)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(4)

    def h2(text: str, color=None):
        c = color or pri
        sf("B", 14)
        pdf.set_text_color(*c)
        pdf.multi_cell(0, 7, text, align="L")
        pdf.set_text_color(30, 30, 30)
        pdf.ln(1)

    def body(text: str, size=10, italic=False, color=(30, 30, 30), indent=0):
        style = "I" if italic else ""
        sf(style, size)
        pdf.set_text_color(*color)
        if indent:
            pdf.set_x(_LM + indent)
            pdf.multi_cell(_USABLE - indent, 5.5, text, align="J")
        else:
            pdf.multi_cell(0, 5.5, text, align="J")
        pdf.set_text_color(30, 30, 30)

    def accent_bar(height=1, color=None):
        c = color or sec
        y = pdf.get_y()
        pdf.set_fill_color(*c)
        pdf.rect(_LM, y, _USABLE, height, style="F")
        pdf.ln(height + 2)

    def pill_row(items, color=None):
        """Inline pill chips on one row."""
        c = color or pri
        lt = _lighter(c, factor=0.22)
        sf("B", 8)
        x = _LM
        y = pdf.get_y()
        for item in items:
            w = pdf.get_string_width(item) + 8
            if x + w > _PW - _RM:
                x = _LM
                y += 9
            pdf.set_fill_color(*lt)
            pdf.rect(x, y, w, 7, style="F")
            pdf.set_xy(x + 1, y)
            pdf.set_text_color(*c)
            pdf.cell(w - 2, 7, item, align="C")
            x += w + 4
        pdf.set_text_color(30, 30, 30)
        pdf.set_y(y + 10)

    def num_badge(number: int, color=None):
        """Circle badge with number (drawn before the text row)."""
        c = color or pri
        r = 5
        cx = _LM + r
        cy = pdf.get_y() + r + 1
        pdf.set_fill_color(*c)
        pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style="F")
        sf("B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(cx - r, cy - r)
        pdf.cell(r * 2, r * 2, str(number), align="C")
        pdf.set_text_color(30, 30, 30)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 1 — COVER
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Top banner (55 mm)
    pdf.set_fill_color(*pri)
    pdf.rect(0, 0, _PW, 55, style="F")

    # Thin accent strip
    pdf.set_fill_color(*sec)
    pdf.rect(0, 55, _PW, 4, style="F")

    # Subject label
    pdf.set_y(12)
    sf("B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 6, subject.upper(), align="C", ln=True)
    pdf.ln(2)

    # Topic title
    sf("B", 26)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(0, 12, topic, align="C")
    pdf.ln(2)

    # Read time note
    words = sum(len((state.get(k) or "").split()) for k in ("brief_summary", "article_content"))
    read_min = max(1, round(words / 200))
    sf("", 8)
    pdf.set_text_color(200, 220, 255)
    pdf.cell(0, 5, f"{read_min} min read", align="C", ln=True)

    # Below banner
    pdf.set_y(68)
    sf("", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 6, "A Study Buddy deep-dive into this topic - facts, illustrations, quiz & more.", align="C")
    pdf.ln(6)

    # Concept pills
    if concepts:
        pill_row(concepts[:7], color=pri)

    # Spacer + branding at bottom of cover
    pdf.set_y(_PH - 30)
    pdf.set_fill_color(*_lighter(pri, factor=0.1))
    pdf.rect(0, _PH - 22, _PW, 22, style="F")
    pdf.set_y(_PH - 16)
    sf("B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, "Study Buddy AI  *  Powered by Groq", align="C", ln=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 2 — AT A GLANCE
    # ══════════════════════════════════════════════════════════════════════════
    if summary or concepts:
        pdf.add_page()
        sec_bar("At a Glance", color=pri)

        if summary:
            body(summary, size=11)
            pdf.ln(5)

        if concepts:
            sf("B", 9)
            pdf.set_text_color(*pri)
            pdf.cell(0, 6, "KEY CONCEPTS", ln=True)
            pdf.ln(2)
            for i, c in enumerate(concepts):
                sf("B", 10)
                pdf.set_text_color(*pri)
                pdf.set_x(_LM)
                pdf.cell(6, 6, "-", ln=False)
                pdf.set_text_color(30, 30, 30)
                sf("", 10)
                pdf.multi_cell(0, 6, c, align="L")
            pdf.set_text_color(30, 30, 30)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 3 — FASCINATING FACTS
    # ══════════════════════════════════════════════════════════════════════════
    if facts:
        pdf.add_page()
        sec_bar("Fascinating Facts", color=sec)

        colors = [pri, sec, pri, sec, pri]
        for i, f in enumerate(facts):
            fact_text = _clean(f.get("fact", ""))
            wow_text  = _clean(f.get("wow_factor", ""))
            c = colors[i % len(colors)]
            lt = _lighter(c, factor=0.2)

            y_start = pdf.get_y()
            # Coloured left border strip
            pdf.set_fill_color(*c)
            pdf.rect(_LM, y_start, 3, 22, style="F")
            # Light background card
            pdf.set_fill_color(*lt)
            pdf.rect(_LM + 3, y_start, _USABLE - 3, 22, style="F")

            # Number
            pdf.set_xy(_LM + 5, y_start + 2)
            sf("B", 14)
            pdf.set_text_color(*c)
            pdf.cell(10, 8, f"{i+1:02d}", ln=False)

            # Fact text
            pdf.set_xy(_LM + 17, y_start + 2)
            sf("B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(_USABLE - 20, 5, fact_text, align="L")

            # Wow factor
            wow_y = max(pdf.get_y(), y_start + 12)
            pdf.set_xy(_LM + 17, wow_y)
            sf("I", 9)
            pdf.set_text_color(*c)
            pdf.multi_cell(_USABLE - 20, 5, wow_text, align="L")

            pdf.set_text_color(30, 30, 30)
            pdf.set_y(max(pdf.get_y(), y_start + 24))
            pdf.ln(3)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 4 — ILLUSTRATED GUIDE (visual descriptions, no images)
    # ══════════════════════════════════════════════════════════════════════════
    if visuals:
        pdf.add_page()
        sec_bar("Illustrated Guide", color=pri)

        roman = ["I", "II", "III", "IV"]
        for i, v in enumerate(visuals[:4]):
            title_v = _clean(v.get("title", ""))
            desc_v  = _clean(v.get("description", ""))
            helps_v = _clean(v.get("how_it_helps", ""))
            vtype   = _clean(v.get("type", ""))
            terms   = [_clean(s) for s in v.get("search_terms", [])[:3]]

            y_start = pdf.get_y()
            lt = _lighter(pri, factor=0.18)
            pdf.set_fill_color(*lt)
            pdf.rect(_LM, y_start, _USABLE, 28, style="F")
            pdf.set_fill_color(*sec)
            pdf.rect(_LM, y_start, _USABLE, 4, style="F")

            # Plate label
            pdf.set_xy(_LM + 4, y_start + 5)
            sf("B", 8)
            pdf.set_text_color(*sec)
            pdf.cell(30, 5, f"PLATE {roman[i]}  |  {vtype.upper()}", ln=False)

            # Title
            pdf.set_xy(_LM + 4, y_start + 12)
            sf("B", 11)
            pdf.set_text_color(*pri)
            pdf.multi_cell(_USABLE - 8, 5.5, title_v, align="L")

            # Description
            pdf.set_x(_LM + 4)
            sf("", 9)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(_USABLE - 8, 4.5, desc_v, align="L")

            # Why it helps
            if helps_v:
                pdf.set_x(_LM + 4)
                sf("I", 9)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(_USABLE - 8, 4.5, helps_v, align="L")

            pdf.set_text_color(30, 30, 30)
            pdf.set_y(max(pdf.get_y(), y_start + 30))
            pdf.ln(4)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 5 — KEY TAKEAWAYS
    # ══════════════════════════════════════════════════════════════════════════
    if tks:
        pdf.add_page()
        sec_bar("What to Remember", color=pri)

        for i, tk in enumerate(tks):
            point = _clean(tk.get("point", ""))
            why   = _clean(tk.get("why_important", ""))
            c     = pri if i % 2 == 0 else sec
            lt    = _lighter(c, factor=0.2)

            y_start = pdf.get_y()
            # Colour strip + card bg
            pdf.set_fill_color(*c)
            pdf.rect(_LM, y_start, 12, 22, style="F")
            pdf.set_fill_color(*lt)
            pdf.rect(_LM + 12, y_start, _USABLE - 12, 22, style="F")

            # Number inside badge
            sf("B", 14)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(_LM, y_start + 4)
            pdf.cell(12, 8, str(i + 1), align="C", ln=False)

            # Point text
            pdf.set_xy(_LM + 15, y_start + 2)
            sf("B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(_USABLE - 18, 5.5, point, align="L")

            # Why important
            why_y = max(pdf.get_y(), y_start + 12)
            pdf.set_xy(_LM + 15, why_y)
            sf("I", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(_USABLE - 18, 5, why, align="L")

            pdf.set_text_color(30, 30, 30)
            pdf.set_y(max(pdf.get_y(), y_start + 24))
            pdf.ln(3)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 6 — QUIZ
    # ══════════════════════════════════════════════════════════════════════════
    if quiz:
        pdf.add_page()
        sec_bar("Test Yourself", color=sec)

        for qi, q in enumerate(quiz):
            question = _clean(q.get("question", ""))
            options  = q.get("options", [])
            answer   = _clean(q.get("answer", "A"))
            expl     = _clean(q.get("explanation", ""))

            lt = _lighter(pri, factor=0.18)
            y_start = pdf.get_y()

            # Q badge + question
            pdf.set_fill_color(*pri)
            pdf.rect(_LM, y_start, 14, 10, style="F")
            pdf.set_xy(_LM, y_start)
            sf("B", 9)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(14, 10, f"Q{qi+1}", align="C", ln=False)

            pdf.set_xy(_LM + 16, y_start + 1)
            sf("B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(_USABLE - 18, 5.5, question, align="L")
            pdf.ln(2)

            # Options
            for opt in options:
                opt_text = _clean(opt)
                letter   = opt_text[0] if opt_text else ""
                is_ans   = letter == answer
                pdf.set_x(_LM + 5)
                if is_ans:
                    sf("B", 10)
                    pdf.set_text_color(*pri)
                    prefix = f">> {opt_text}"   # answer indicator
                else:
                    sf("", 10)
                    pdf.set_text_color(80, 80, 80)
                    prefix = f"   {opt_text}"
                pdf.multi_cell(_USABLE - 8, 5.5, prefix, align="L")
            pdf.set_text_color(30, 30, 30)

            # Explanation
            if expl:
                pdf.ln(1)
                pdf.set_x(_LM + 5)
                sf("I", 9)
                pdf.set_text_color(90, 90, 90)
                pdf.multi_cell(_USABLE - 8, 5, f"Explanation: {expl}", align="L")
                pdf.set_text_color(30, 30, 30)

            pdf.ln(5)
            accent_bar(height=0.5, color=sec)
            pdf.ln(3)

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 7 — IN DEPTH (Article)
    # ══════════════════════════════════════════════════════════════════════════
    if a_body:
        pdf.add_page()
        sec_bar("In Depth", color=pri)
        h2(a_title, color=pri)
        accent_bar(height=3, color=sec)
        pdf.ln(2)

        for para in re.split(r"\n{2,}", a_body.strip()):
            para = para.strip()
            if not para:
                continue
            # Section headings inside article body
            if para.startswith("##") or para.startswith("#"):
                heading = para.lstrip("#").strip()
                pdf.ln(3)
                sf("B", 12)
                pdf.set_text_color(*pri)
                pdf.multi_cell(0, 6, heading, align="L")
                accent_bar(height=1, color=_lighter(pri, factor=0.35))
                pdf.set_text_color(30, 30, 30)
            else:
                body(para, size=10)
                pdf.ln(1)

    # ══════════════════════════════════════════════════════════════════════════
    #  FINAL PAGE — CLOSING
    # ══════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    # Full-page coloured background
    pdf.set_fill_color(*pri)
    pdf.rect(0, 0, _PW, _PH, style="F")
    pdf.set_fill_color(*sec)
    pdf.rect(0, _PH - 8, _PW, 8, style="F")

    closing_quote = (
        _clean(tks[0].get("point", "")) if tks
        else "Keep questioning. Keep exploring."
    )

    pdf.set_y(_PH // 2 - 35)
    # Decorative stars
    sf("", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "*  *  *", align="C", ln=True)
    pdf.ln(6)

    sf("B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(0, 9, f'"{closing_quote}"', align="C")
    pdf.ln(10)

    sf("I", 11)
    pdf.set_text_color(200, 220, 255)
    pdf.multi_cell(0, 6,
        "Keep questioning. Keep exploring. The more you learn,\n"
        "the more the world opens up to you.", align="C")
    pdf.ln(14)

    sf("B", 9)
    pdf.set_text_color(180, 200, 240)
    pdf.cell(0, 6, "STUDY BUDDY AI  *  POWERED BY GROQ", align="C", ln=True)

    return bytes(pdf.output())
