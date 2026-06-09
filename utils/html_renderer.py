"""
Study Buddy AI — Book-style HTML renderer.
DK Eyewitness / NatGeo Kids aesthetic: bold colors, inline SVG illustrations,
no external links, optimised for print as a student textbook.
"""
import html
import re

# ── Subject themes (pri = dominant, sec = accent, bg = light fill) ────────────
_THEMES = {
    "science":     dict(pri="#0277BD", sec="#F57C00", bg="#E1F5FE", lt="#B3E5FC", dk="#01579B"),
    "biology":     dict(pri="#2E7D32", sec="#F9A825", bg="#E8F5E9", lt="#C8E6C9", dk="#1B5E20"),
    "chemistry":   dict(pri="#6A1B9A", sec="#F4511E", bg="#F3E5F5", lt="#E1BEE7", dk="#4A148C"),
    "physics":     dict(pri="#1565C0", sec="#E91E63", bg="#E3F2FD", lt="#BBDEFB", dk="#0D47A1"),
    "mathematics": dict(pri="#4527A0", sec="#00ACC1", bg="#EDE7F6", lt="#D1C4E9", dk="#311B92"),
    "history":     dict(pri="#6D4C41", sec="#F4511E", bg="#EFEBE9", lt="#D7CCC8", dk="#3E2723"),
    "geography":   dict(pri="#00695C", sec="#E53935", bg="#E0F2F1", lt="#B2DFDB", dk="#004D40"),
    "english":     dict(pri="#33691E", sec="#7B1FA2", bg="#F1F8E9", lt="#DCEDC8", dk="#1B5E20"),
}
_DEF = dict(pri="#4E342E", sec="#E91E63", bg="#FFF8E1", lt="#FFE0B2", dk="#3E2723")

# ── Subject cover SVGs ────────────────────────────────────────────────────────
_SVG = {
    "science": """<svg viewBox="0 0 100 130" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="38" y="4" width="24" height="11" rx="3" fill="rgba(255,255,255,.6)"/>
      <path d="M42 15 L28 78 L8 118 L92 118 L72 78 L58 15Z" fill="rgba(255,255,255,.12)" stroke="rgba(255,255,255,.75)" stroke-width="2.5"/>
      <path d="M16 96 Q50 84 84 96 L92 118 L8 118Z" fill="rgba(255,255,255,.32)"/>
      <circle cx="34" cy="102" r="5" fill="rgba(255,255,255,.72)"/>
      <circle cx="56" cy="107" r="3.5" fill="rgba(255,255,255,.62)"/>
      <circle cx="67" cy="99" r="4" fill="rgba(255,255,255,.52)"/>
      <circle cx="30" cy="58" r="3" fill="rgba(255,255,255,.42)"/>
      <circle cx="72" cy="54" r="2.5" fill="rgba(255,255,255,.42)"/>
    </svg>""",
    "biology": """<svg viewBox="0 0 80 130" fill="none">
      <path d="M20 8 Q60 28 20 55 Q-8 76 20 102 Q56 122 20 130" stroke="rgba(255,255,255,.9)" stroke-width="3" fill="none"/>
      <path d="M60 8 Q20 28 60 55 Q88 76 60 102 Q24 122 60 130" stroke="rgba(255,255,255,.55)" stroke-width="3" fill="none"/>
      <line x1="27" y1="26" x2="53" y2="26" stroke="rgba(255,255,255,.7)" stroke-width="2.5"/>
      <line x1="20" y1="55" x2="60" y2="55" stroke="rgba(255,255,255,.7)" stroke-width="2.5"/>
      <line x1="27" y1="81" x2="53" y2="81" stroke="rgba(255,255,255,.7)" stroke-width="2.5"/>
      <line x1="20" y1="102" x2="60" y2="102" stroke="rgba(255,255,255,.7)" stroke-width="2.5"/>
    </svg>""",
    "chemistry": """<svg viewBox="0 0 120 120" fill="none">
      <circle cx="60" cy="60" r="10" fill="rgba(255,255,255,.85)"/>
      <ellipse cx="60" cy="60" rx="50" ry="18" stroke="rgba(255,255,255,.75)" stroke-width="2.5" fill="none"/>
      <ellipse cx="60" cy="60" rx="50" ry="18" stroke="rgba(255,255,255,.55)" stroke-width="2.5" fill="none" transform="rotate(60 60 60)"/>
      <ellipse cx="60" cy="60" rx="50" ry="18" stroke="rgba(255,255,255,.55)" stroke-width="2.5" fill="none" transform="rotate(120 60 60)"/>
      <circle cx="110" cy="60" r="7" fill="rgba(255,255,255,.8)"/>
      <circle cx="35" cy="17" r="6" fill="rgba(255,255,255,.65)"/>
      <circle cx="35" cy="103" r="6" fill="rgba(255,255,255,.65)"/>
    </svg>""",
    "physics": """<svg viewBox="0 0 140 100" fill="none">
      <path d="M0 50 Q17 20 35 50 Q53 80 70 50 Q87 20 105 50 Q122 80 140 50" stroke="rgba(255,255,255,.9)" stroke-width="3.5" fill="none"/>
      <path d="M0 65 Q17 35 35 65 Q53 95 70 65 Q87 35 105 65 Q122 95 140 65" stroke="rgba(255,255,255,.42)" stroke-width="2" fill="none"/>
      <line x1="70" y1="8" x2="70" y2="92" stroke="rgba(255,255,255,.32)" stroke-width="1.5" stroke-dasharray="5,4"/>
      <circle cx="35" cy="50" r="5" fill="rgba(255,255,255,.7)"/>
      <circle cx="105" cy="50" r="5" fill="rgba(255,255,255,.7)"/>
    </svg>""",
    "mathematics": """<svg viewBox="0 0 110 110" fill="none">
      <polygon points="55,8 105,98 5,98" stroke="rgba(255,255,255,.9)" stroke-width="3" fill="rgba(255,255,255,.1)"/>
      <circle cx="55" cy="63" r="26" stroke="rgba(255,255,255,.6)" stroke-width="2.5" fill="none"/>
      <line x1="5" y1="63" x2="105" y2="63" stroke="rgba(255,255,255,.38)" stroke-width="1.5"/>
      <line x1="55" y1="8" x2="55" y2="98" stroke="rgba(255,255,255,.38)" stroke-width="1.5"/>
    </svg>""",
    "history": """<svg viewBox="0 0 110 130" fill="none">
      <rect x="8" y="12" width="94" height="12" rx="3" fill="rgba(255,255,255,.6)"/>
      <rect x="8" y="108" width="94" height="12" rx="3" fill="rgba(255,255,255,.6)"/>
      <rect x="14" y="24" width="16" height="84" rx="4" fill="rgba(255,255,255,.32)"/>
      <rect x="47" y="24" width="16" height="84" rx="4" fill="rgba(255,255,255,.32)"/>
      <rect x="80" y="24" width="16" height="84" rx="4" fill="rgba(255,255,255,.32)"/>
    </svg>""",
    "geography": """<svg viewBox="0 0 110 110" fill="none">
      <circle cx="55" cy="55" r="48" stroke="rgba(255,255,255,.8)" stroke-width="2.5" fill="rgba(255,255,255,.08)"/>
      <ellipse cx="55" cy="55" rx="22" ry="48" stroke="rgba(255,255,255,.52)" stroke-width="2" fill="none"/>
      <line x1="7" y1="55" x2="103" y2="55" stroke="rgba(255,255,255,.48)" stroke-width="1.5"/>
      <line x1="13" y1="30" x2="97" y2="30" stroke="rgba(255,255,255,.32)" stroke-width="1.5"/>
      <line x1="13" y1="80" x2="97" y2="80" stroke="rgba(255,255,255,.32)" stroke-width="1.5"/>
    </svg>""",
    "english": """<svg viewBox="0 0 130 90" fill="none">
      <path d="M65 14 Q38 9 8 22 L8 82 Q38 70 65 76Z" fill="rgba(255,255,255,.22)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>
      <path d="M65 14 Q92 9 122 22 L122 82 Q92 70 65 76Z" fill="rgba(255,255,255,.16)" stroke="rgba(255,255,255,.75)" stroke-width="2"/>
      <line x1="65" y1="14" x2="65" y2="76" stroke="rgba(255,255,255,.9)" stroke-width="3"/>
      <line x1="20" y1="38" x2="58" y2="38" stroke="rgba(255,255,255,.4)" stroke-width="1.5"/>
      <line x1="20" y1="50" x2="55" y2="50" stroke="rgba(255,255,255,.4)" stroke-width="1.5"/>
      <line x1="20" y1="62" x2="50" y2="62" stroke="rgba(255,255,255,.4)" stroke-width="1.5"/>
      <line x1="72" y1="38" x2="112" y2="38" stroke="rgba(255,255,255,.4)" stroke-width="1.5"/>
      <line x1="72" y1="50" x2="108" y2="50" stroke="rgba(255,255,255,.4)" stroke-width="1.5"/>
    </svg>""",
    "_default": """<svg viewBox="0 0 90 120" fill="none">
      <circle cx="45" cy="42" r="30" fill="rgba(255,255,255,.18)" stroke="rgba(255,255,255,.75)" stroke-width="2.5"/>
      <path d="M35 72 Q35 86 45 86 Q55 86 55 72" stroke="rgba(255,255,255,.75)" stroke-width="2.5" fill="rgba(255,255,255,.18)"/>
      <line x1="35" y1="86" x2="55" y2="86" stroke="rgba(255,255,255,.7)" stroke-width="2.5"/>
      <line x1="37" y1="94" x2="53" y2="94" stroke="rgba(255,255,255,.55)" stroke-width="2.5"/>
      <line x1="40" y1="102" x2="50" y2="102" stroke="rgba(255,255,255,.4)" stroke-width="2.5"/>
      <line x1="45" y1="4" x2="45" y2="12" stroke="rgba(255,255,255,.55)" stroke-width="2"/>
      <line x1="18" y1="18" x2="23" y2="23" stroke="rgba(255,255,255,.55)" stroke-width="2"/>
      <line x1="72" y1="18" x2="67" y2="23" stroke="rgba(255,255,255,.55)" stroke-width="2"/>
    </svg>""",
}


def _subject_svg(subject: str) -> str:
    s = subject.lower()
    for k in _SVG:
        if k in s:
            return _SVG[k]
    return _SVG["_default"]


def _vis_svg(vtype: str, title: str, pri: str, sec: str, bg: str) -> str:
    """
    Choose and return an inline SVG that looks like the described visual type.
    Uses both vtype and title for smart matching so 'Mind Map' doesn't render
    as a terrain map, 'Word Web' doesn't become a bar chart, etc.
    """
    combined = (vtype + " " + title).lower()

    # ── Mind Map / Word Web / Concept Map / Spider ────────────────────────────
    # Central oval with radiating satellite ovals — unmistakably a mind map.
    if any(k in combined for k in ("mind map", "word web", "concept map", "spider", "web", "bubble")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- centre -->
          <ellipse cx="110" cy="65" rx="36" ry="22" fill="{pri}" opacity=".85"/>
          <!-- top -->
          <ellipse cx="110" cy="16" rx="28" ry="13" fill="{sec}" opacity=".75"/>
          <line x1="110" y1="43" x2="110" y2="29" stroke="{pri}" stroke-width="2"/>
          <!-- bottom -->
          <ellipse cx="110" cy="114" rx="28" ry="13" fill="{sec}" opacity=".75"/>
          <line x1="110" y1="87" x2="110" y2="101" stroke="{pri}" stroke-width="2"/>
          <!-- left -->
          <ellipse cx="34" cy="65" rx="28" ry="13" fill="{sec}" opacity=".75"/>
          <line x1="74" y1="65" x2="62" y2="65" stroke="{pri}" stroke-width="2"/>
          <!-- right -->
          <ellipse cx="186" cy="65" rx="28" ry="13" fill="{sec}" opacity=".75"/>
          <line x1="146" y1="65" x2="158" y2="65" stroke="{pri}" stroke-width="2"/>
          <!-- top-left -->
          <ellipse cx="48" cy="28" rx="22" ry="11" fill="{pri}" opacity=".4"/>
          <line x1="80" y1="50" x2="67" y2="37" stroke="{pri}" stroke-width="1.5"/>
          <!-- bottom-right -->
          <ellipse cx="172" cy="102" rx="22" ry="11" fill="{pri}" opacity=".4"/>
          <line x1="140" y1="80" x2="153" y2="93" stroke="{pri}" stroke-width="1.5"/>
        </svg>"""

    # ── Table / Grid / Example Table / Matrix ─────────────────────────────────
    # A clear table with a coloured header row + 3 data rows and 3 columns.
    if any(k in combined for k in ("table", "grid", "matrix", "example table")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- header row -->
          <rect x="10" y="12" width="200" height="26" rx="4" fill="{pri}" opacity=".85"/>
          <!-- col dividers in header -->
          <line x1="77"  y1="12" x2="77"  y2="38" stroke="rgba(255,255,255,.5)" stroke-width="1.5"/>
          <line x1="144" y1="12" x2="144" y2="38" stroke="rgba(255,255,255,.5)" stroke-width="1.5"/>
          <!-- data rows -->
          <rect x="10" y="42" width="200" height="24" fill="{pri}" opacity=".1"/>
          <rect x="10" y="70" width="200" height="24" fill="{pri}" opacity=".18"/>
          <rect x="10" y="98" width="200" height="24" fill="{pri}" opacity=".1"/>
          <!-- vertical col dividers -->
          <line x1="77"  y1="42" x2="77"  y2="122" stroke="{pri}" stroke-width="1" opacity=".3"/>
          <line x1="144" y1="42" x2="144" y2="122" stroke="{pri}" stroke-width="1" opacity=".3"/>
          <!-- outer border -->
          <rect x="10" y="12" width="200" height="110" rx="4" fill="none" stroke="{pri}" stroke-width="2" opacity=".6"/>
          <!-- row separator lines -->
          <line x1="10" y1="66" x2="210" y2="66" stroke="{pri}" stroke-width="1" opacity=".25"/>
          <line x1="10" y1="94" x2="210" y2="94" stroke="{pri}" stroke-width="1" opacity=".25"/>
          <!-- text-like dashes in cells to suggest content -->
          <rect x="20" y="50" width="40" height="6" rx="3" fill="{pri}" opacity=".35"/>
          <rect x="88" y="50" width="38" height="6" rx="3" fill="{pri}" opacity=".35"/>
          <rect x="155" y="50" width="38" height="6" rx="3" fill="{sec}" opacity=".55"/>
          <rect x="20" y="78" width="40" height="6" rx="3" fill="{pri}" opacity=".3"/>
          <rect x="88" y="78" width="38" height="6" rx="3" fill="{sec}" opacity=".45"/>
          <rect x="155" y="78" width="38" height="6" rx="3" fill="{pri}" opacity=".3"/>
          <rect x="20" y="106" width="40" height="6" rx="3" fill="{pri}" opacity=".35"/>
          <rect x="88" y="106" width="38" height="6" rx="3" fill="{pri}" opacity=".3"/>
          <rect x="155" y="106" width="38" height="6" rx="3" fill="{sec}" opacity=".4"/>
        </svg>"""

    # ── Timeline / Chronology / Sequence ──────────────────────────────────────
    # Horizontal axis with 4 labelled event dots alternating above/below.
    if any(k in combined for k in ("timeline", "chronolog", "sequence", "history", "era", "period")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- axis line with arrow -->
          <line x1="14" y1="65" x2="202" y2="65" stroke="{pri}" stroke-width="3" opacity=".7"/>
          <polygon points="200,60 212,65 200,70" fill="{pri}" opacity=".7"/>
          <!-- event 1 — above -->
          <circle cx="44"  cy="65" r="8" fill="{pri}"/>
          <line x1="44" y1="57" x2="44" y2="30" stroke="{pri}" stroke-width="1.5" stroke-dasharray="3,2"/>
          <rect x="20" y="16" width="48" height="16" rx="4" fill="{sec}" opacity=".7"/>
          <!-- event 2 — below -->
          <circle cx="90"  cy="65" r="8" fill="{sec}"/>
          <line x1="90" y1="73" x2="90" y2="98" stroke="{sec}" stroke-width="1.5" stroke-dasharray="3,2"/>
          <rect x="66" y="98" width="48" height="16" rx="4" fill="{pri}" opacity=".5"/>
          <!-- event 3 — above -->
          <circle cx="136" cy="65" r="8" fill="{pri}"/>
          <line x1="136" y1="57" x2="136" y2="30" stroke="{pri}" stroke-width="1.5" stroke-dasharray="3,2"/>
          <rect x="112" y="16" width="48" height="16" rx="4" fill="{sec}" opacity=".7"/>
          <!-- event 4 — below -->
          <circle cx="182" cy="65" r="8" fill="{sec}"/>
          <line x1="182" y1="73" x2="182" y2="98" stroke="{sec}" stroke-width="1.5" stroke-dasharray="3,2"/>
          <rect x="158" y="98" width="48" height="16" rx="4" fill="{pri}" opacity=".5"/>
        </svg>"""

    # ── Venn Diagram / Compare / Overlap ──────────────────────────────────────
    if any(k in combined for k in ("venn", "compare", "overlap", "versus", "vs", "differ", "similar")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <circle cx="82"  cy="65" r="52" fill="{pri}" opacity=".28" stroke="{pri}" stroke-width="2.5"/>
          <circle cx="138" cy="65" r="52" fill="{sec}" opacity=".28" stroke="{sec}" stroke-width="2.5"/>
          <!-- overlap highlight -->
          <path d="M110 20 Q132 35 132 65 Q132 95 110 110 Q88 95 88 65 Q88 35 110 20Z"
                fill="{pri}" opacity=".22"/>
          <!-- label dashes -->
          <rect x="30"  y="60" width="32" height="6" rx="3" fill="{pri}" opacity=".6"/>
          <rect x="158" y="60" width="32" height="6" rx="3" fill="{sec}" opacity=".6"/>
          <rect x="96"  y="57" width="28" height="6" rx="3" fill="{pri}" opacity=".45"/>
          <rect x="96"  y="67" width="28" height="6" rx="3" fill="{sec}" opacity=".45"/>
        </svg>"""

    # ── Cycle / Process Cycle ─────────────────────────────────────────────────
    if any(k in combined for k in ("cycle", "circular", "loop", "process")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- dashed circle guide -->
          <circle cx="110" cy="65" r="46" fill="none" stroke="{pri}" stroke-width="1.5"
                  stroke-dasharray="5,4" opacity=".35"/>
          <!-- 4 step boxes at compass points -->
          <!-- top -->
          <rect x="82" y="8"  width="56" height="24" rx="6" fill="{pri}" opacity=".8"/>
          <!-- right -->
          <rect x="150" y="53" width="56" height="24" rx="6" fill="{sec}" opacity=".7"/>
          <!-- bottom -->
          <rect x="82" y="98" width="56" height="24" rx="6" fill="{pri}" opacity=".65"/>
          <!-- left -->
          <rect x="14" y="53" width="56" height="24" rx="6" fill="{sec}" opacity=".7"/>
          <!-- arrows (curved via path) -->
          <!-- top → right -->
          <path d="M138 20 Q168 20 168 53" fill="none" stroke="{pri}" stroke-width="2.5"/>
          <polygon points="163,52 170,53 165,60" fill="{pri}"/>
          <!-- right → bottom -->
          <path d="M168 77 Q168 98 138 110" fill="none" stroke="{sec}" stroke-width="2.5"/>
          <polygon points="139,116 138,110 131,113" fill="{sec}"/>
          <!-- bottom → left -->
          <path d="M82 110 Q52 110 52 77" fill="none" stroke="{pri}" stroke-width="2.5"/>
          <polygon points="47,78 52,77 55,70" fill="{pri}"/>
          <!-- left → top -->
          <path d="M52 53 Q52 20 82 20" fill="none" stroke="{sec}" stroke-width="2.5"/>
          <polygon points="81,14 82,20 89,17" fill="{sec}"/>
        </svg>"""

    # ── Bar / Column Chart ────────────────────────────────────────────────────
    if any(k in combined for k in ("chart", "graph", "bar", "column", "usage", "statistic", "data")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- grid lines -->
          <line x1="30" y1="20" x2="210" y2="20" stroke="{pri}" stroke-width="1" opacity=".15"/>
          <line x1="30" y1="45" x2="210" y2="45" stroke="{pri}" stroke-width="1" opacity=".15"/>
          <line x1="30" y1="70" x2="210" y2="70" stroke="{pri}" stroke-width="1" opacity=".15"/>
          <!-- axes -->
          <line x1="30" y1="15" x2="30" y2="105" stroke="{pri}" stroke-width="2.5"/>
          <line x1="30" y1="105" x2="215" y2="105" stroke="{pri}" stroke-width="2.5"/>
          <!-- bars -->
          <rect x="44"  y="58" width="30" height="47" fill="{pri}" opacity=".55" rx="3"/>
          <rect x="88"  y="28" width="30" height="77" fill="{pri}" opacity=".78" rx="3"/>
          <rect x="132" y="42" width="30" height="63" fill="{sec}" opacity=".72" rx="3"/>
          <rect x="176" y="18" width="30" height="87" fill="{pri}" opacity=".92" rx="3"/>
          <!-- tick marks on Y axis -->
          <line x1="26" y1="20" x2="30" y2="20" stroke="{pri}" stroke-width="1.5" opacity=".5"/>
          <line x1="26" y1="45" x2="30" y2="45" stroke="{pri}" stroke-width="1.5" opacity=".5"/>
          <line x1="26" y1="70" x2="30" y2="70" stroke="{pri}" stroke-width="1.5" opacity=".5"/>
        </svg>"""

    # ── Flow Diagram / Flowchart ──────────────────────────────────────────────
    if any(k in combined for k in ("diagram", "flow", "flowchart", "step", "process step")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- Start oval -->
          <ellipse cx="30" cy="65" rx="22" ry="14" fill="{pri}" opacity=".75"/>
          <!-- arrow 1 -->
          <line x1="52" y1="65" x2="68" y2="65" stroke="{pri}" stroke-width="2"/>
          <polygon points="66,61 74,65 66,69" fill="{pri}"/>
          <!-- Process rect 1 -->
          <rect x="74" y="51" width="50" height="28" rx="5" fill="{pri}" opacity=".22" stroke="{pri}" stroke-width="2"/>
          <!-- arrow 2 -->
          <line x1="124" y1="65" x2="140" y2="65" stroke="{pri}" stroke-width="2"/>
          <polygon points="138,61 146,65 138,69" fill="{pri}"/>
          <!-- Decision diamond -->
          <polygon points="155,48 178,65 155,82 132,65" fill="{sec}" opacity=".3" stroke="{sec}" stroke-width="2"/>
          <!-- Yes arrow down from diamond -->
          <line x1="155" y1="82" x2="155" y2="100" stroke="{sec}" stroke-width="2"/>
          <polygon points="151,98 155,108 159,98" fill="{sec}"/>
          <rect x="130" y="108" width="50" height="18" rx="5" fill="{sec}" opacity=".4"/>
          <!-- No arrow right from diamond -->
          <line x1="178" y1="65" x2="198" y2="65" stroke="{pri}" stroke-width="2"/>
          <ellipse cx="208" cy="65" rx="12" ry="10" fill="{pri}" opacity=".65"/>
        </svg>"""

    # ── Geographic Map ────────────────────────────────────────────────────────
    if any(k in combined for k in ("geographic map", "location map", "world map", "country map",
                                   "region", "territory", "geography map")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <path d="M0 90 Q40 70 90 82 Q130 94 165 66 Q188 48 220 60 L220 130 L0 130Z" fill="{pri}" opacity=".3"/>
          <path d="M0 72 Q50 54 100 66 Q140 78 175 48 Q196 30 220 40 L220 130 L0 130Z" fill="{pri}" opacity=".2"/>
          <circle cx="72"  cy="48" r="18" fill="{sec}" opacity=".4" stroke="{sec}" stroke-width="1.5"/>
          <circle cx="158" cy="38" r="12" fill="{pri}" opacity=".5" stroke="{pri}" stroke-width="1.5"/>
          <!-- pin markers -->
          <circle cx="72"  cy="38" r="5" fill="{sec}"/>
          <polygon points="67,38 77,38 72,50" fill="{sec}"/>
          <circle cx="158" cy="29" r="4" fill="{pri}"/>
          <polygon points="154,29 162,29 158,40" fill="{pri}"/>
        </svg>"""

    # ── Infographic / Stats Infographic ──────────────────────────────────────
    if any(k in combined for k in ("infographic", "info", "visual summary", "fact sheet")):
        return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
          <rect width="220" height="130" fill="{bg}"/>
          <!-- centre hub -->
          <circle cx="110" cy="65" r="22" fill="{pri}" opacity=".82"/>
          <!-- 4 satellite blocks -->
          <rect x="10"  y="10"  width="60" height="36" rx="8" fill="{sec}" opacity=".65"/>
          <rect x="150" y="10"  width="60" height="36" rx="8" fill="{sec}" opacity=".65"/>
          <rect x="10"  y="84"  width="60" height="36" rx="8" fill="{pri}" opacity=".45"/>
          <rect x="150" y="84"  width="60" height="36" rx="8" fill="{pri}" opacity=".45"/>
          <!-- connector lines -->
          <line x1="88"  y1="52" x2="70"  y2="40" stroke="{pri}" stroke-width="2" opacity=".55"/>
          <line x1="132" y1="52" x2="150" y2="40" stroke="{pri}" stroke-width="2" opacity=".55"/>
          <line x1="88"  y1="78" x2="70"  y2="95" stroke="{pri}" stroke-width="2" opacity=".55"/>
          <line x1="132" y1="78" x2="150" y2="95" stroke="{pri}" stroke-width="2" opacity=".55"/>
          <!-- dashes inside satellite blocks to suggest numbers/text -->
          <rect x="22"  y="22" width="30" height="7" rx="3" fill="rgba(255,255,255,.7)"/>
          <rect x="162" y="22" width="30" height="7" rx="3" fill="rgba(255,255,255,.7)"/>
          <rect x="22"  y="95" width="30" height="7" rx="3" fill="rgba(255,255,255,.6)"/>
          <rect x="162" y="95" width="30" height="7" rx="3" fill="rgba(255,255,255,.6)"/>
        </svg>"""

    # ── Default / Illustration / Concept Illustration ─────────────────────────
    return f"""<svg viewBox="0 0 220 130" xmlns="http://www.w3.org/2000/svg">
      <rect width="220" height="130" fill="{bg}"/>
      <!-- large decorative shape -->
      <circle cx="110" cy="65" r="50" fill="none" stroke="{pri}" stroke-width="2.5" opacity=".4"/>
      <circle cx="110" cy="65" r="34" fill="none" stroke="{sec}" stroke-width="2"   opacity=".5"/>
      <circle cx="110" cy="65" r="18" fill="{pri}" opacity=".35"/>
      <!-- 3 accent dots on outer ring -->
      <circle cx="110" cy="15" r="7" fill="{sec}" opacity=".75"/>
      <circle cx="153" cy="91" r="7" fill="{sec}" opacity=".65"/>
      <circle cx="67"  cy="91" r="7" fill="{sec}" opacity=".65"/>
      <!-- connecting radials -->
      <line x1="110" y1="47" x2="110" y2="22" stroke="{pri}" stroke-width="1.5" opacity=".4"/>
      <line x1="126" y1="76" x2="146" y2="85" stroke="{pri}" stroke-width="1.5" opacity=".4"/>
      <line x1="94"  y1="76" x2="74"  y2="85" stroke="{pri}" stroke-width="1.5" opacity=".4"/>
    </svg>"""


def _theme(subject: str) -> dict:
    s = subject.lower()
    for k, v in _THEMES.items():
        if k in s:
            return v
    return _DEF


def _e(x) -> str:
    return html.escape(str(x or ""), quote=False)


def _md(text: str) -> str:
    t = _e(text)
    t = re.sub(r"(?m)^# (.+)$",      r'<h2 class="ah1">\1</h2>', t)
    t = re.sub(r"(?m)^## (.+)$",     r'<h3 class="ah2">\1</h3>', t)
    t = re.sub(r"(?m)^### (.+)$",    r'<h4 class="ah3">\1</h4>', t)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", t)
    t = re.sub(r"\*\*(.+?)\*\*",     r"<strong>\1</strong>",          t)
    t = re.sub(r"\*(.+?)\*",         r"<em>\1</em>",                  t)
    out = []
    for b in re.split(r"\n{2,}", t.strip()):
        b = b.strip()
        if not b:
            continue
        if b.startswith("<h"):
            out.append(b)
        elif b.startswith("**Fun Fact"):
            out.append(f'<div class="funfact">{b}</div>')
        else:
            out.append(f'<p class="ap">{b.replace(chr(10), " ")}</p>')
    return "\n".join(out)


def _rtime(state: dict) -> int:
    words = sum(len((state.get(k) or "").split()) for k in ("brief_summary", "article_content"))
    return max(1, round(words / 200))


# ── COVER ─────────────────────────────────────────────────────────────────────

def _cover(topic, subject, concepts, read_min, t):
    tags = "".join(f'<span class="ctag">{_e(c)}</span>' for c in concepts[:6])
    svg  = _subject_svg(subject)
    return f"""
<section class="page" id="cover">
  <div class="cover-top" style="background:linear-gradient(145deg,{t['pri']},{t['dk']})">
    <div class="subj-badge">{_e(subject)}</div>
    <div class="cov-svg">{svg}</div>
    <h1 class="cov-title">{_e(topic)}</h1>
    <p class="cov-meta">&#128214;&nbsp;{read_min} min read</p>
  </div>
  <div class="cover-bot" style="border-top:6px solid {t['sec']}">
    <p class="cov-intro">A Study Buddy deep-dive into this topic — facts, illustrations, quiz and more.</p>
    <div class="ctags">{tags}</div>
  </div>
</section>"""


# ── OVERVIEW ──────────────────────────────────────────────────────────────────

def _overview(summary, concepts, subject, t, pn):
    if not summary:
        return ""
    icons = ["&#128161;","&#128300;","&#128208;","&#127758;","&#128221;","&#128273;","&#9889;","&#129504;","&#128301;","&#127919;"]
    ccards = "".join(
        f'<div class="concept-card" style="border-color:{t["pri"]}">'
        f'<span class="cc-icon">{icons[i % len(icons)]}</span>'
        f'<span class="cc-name">{_e(c)}</span></div>'
        for i, c in enumerate(concepts)
    )
    first = _e(summary[0]) if summary else ""
    rest  = _e(summary[1:]) if len(summary) > 1 else ""
    return f"""
<section class="page" id="overview">
  <div class="sec-header" style="background:{t['pri']}">
    <span class="sec-label">At a Glance</span>
  </div>
  <div class="pi">
    <div class="two-col">
      <div class="col-main">
        <p class="body-text"><span class="dropcap" style="color:{t['pri']};border-color:{t['lt']};background:{t['bg']}">{first}</span>{rest}</p>
        <div class="pull-quote" style="border-color:{t['sec']};background:{t['bg']}">
          <span class="pq-mark" style="color:{t['sec']}">"</span>
          <p class="pq-text" style="color:{t['dk']}">Understanding <em>{_e(subject)}</em> opens a window
          to ideas that shape the world around us every day.</p>
        </div>
      </div>
      <div class="col-side">
        <p class="side-label" style="color:{t['pri']}">KEY CONCEPTS</p>
        <div class="concepts-list">{ccards}</div>
      </div>
    </div>
    <div class="pn">{pn}</div>
  </div>
</section>"""


# ── FACTS — 5 distinct card styles ────────────────────────────────────────────

_FACT_LABELS = [
    "&#9889;&nbsp;DISCOVERY",
    "&#11088;&nbsp;AMAZING",
    "&#10068;&nbsp;DID YOU KNOW",
    "&#10003;&nbsp;TRUE FACT",
    "&#129327;&nbsp;MIND BLOWN",
]


def _fact_card(i: int, f: dict, t: dict) -> str:
    em   = _e(f.get("emoji", "&#128161;"))
    fact = _e(f.get("fact", ""))
    wow  = _e(f.get("wow_factor", ""))
    lbl  = _FACT_LABELS[i % len(_FACT_LABELS)]

    if i == 0:
        # CARD 1 — HERO: full-width gradient, white text, large emoji on right
        return f"""
<div class="fc-hero" style="background:linear-gradient(135deg,{t['pri']},{t['dk']})">
  <div class="fc-h-body">
    <span class="fc-badge fc-b-white">{lbl}</span>
    <p class="fc-h-fact">{fact}</p>
    <p class="fc-h-wow">&#8220;{wow}&#8221;</p>
  </div>
  <div class="fc-h-em">{em}</div>
</div>"""

    if i == 1:
        # CARD 2 — BIG NUMBER: solid colored left column with huge number
        return f"""
<div class="fc-numcard">
  <div class="fc-numcol" style="background:{t['pri']}">
    <span class="fc-bignum">0{i+1}</span>
  </div>
  <div class="fc-ncbody">
    <span class="fc-badge" style="background:{t['lt']};color:{t['dk']}">{lbl}</span>
    <p class="fc-ncfact">{fact}</p>
    <p class="fc-ncwow" style="color:{t['pri']}">{wow}</p>
  </div>
</div>"""

    if i == 2:
        # CARD 3 — EMOJI STAR: giant centered emoji, tinted background
        return f"""
<div class="fc-emcard" style="background:{t['bg']};border:2px solid {t['lt']}">
  <div class="fc-emicon">{em}</div>
  <span class="fc-badge" style="background:{t['sec']}28;color:{t['sec']}">{lbl}</span>
  <p class="fc-emfact">{fact}</p>
  <p class="fc-emwow" style="color:{t['sec']}">{wow}</p>
</div>"""

    if i == 3:
        # CARD 4 — QUOTE: oversized decorative quote mark, italic fact text
        return f"""
<div class="fc-qcard" style="border-left:5px solid {t['dk']}">
  <div class="fc-qdeco" style="color:{t['dk']}">&ldquo;</div>
  <div class="fc-qbody">
    <span class="fc-badge" style="background:{t['dk']}22;color:{t['dk']}">{lbl}</span>
    <p class="fc-qfact">{fact}</p>
    <p class="fc-qwow" style="color:{t['dk']}">{wow}</p>
  </div>
</div>"""

    # CARD 5 — SPOTLIGHT: accent background, wow factor large + bold
    return f"""
<div class="fc-spotlight" style="background:{t['sec']}1a;border:2px solid {t['sec']}55">
  <div class="fc-sphead">
    <span class="fc-badge" style="background:{t['sec']};color:#fff">{lbl}</span>
    <span class="fc-spem">{em}</span>
  </div>
  <p class="fc-spfact">{fact}</p>
  <p class="fc-spwow" style="color:{t['sec']}">{wow}</p>
</div>"""


def _facts_page(facts, t, pn):
    if not facts:
        return ""
    cards = "".join(_fact_card(i, f, t) for i, f in enumerate(facts[:5]))
    return f"""
<section class="page" id="facts">
  <div class="sec-header" style="background:{t['sec']}">
    <span class="sec-label">Fascinating Facts</span>
  </div>
  <div class="pi">
    <div class="facts-grid">{cards}</div>
    <div class="pn">{pn}</div>
  </div>
</section>"""


# ── VISUALS (no links — SVG illustrations) ────────────────────────────────────

def _visuals_page(visuals, t, pn):
    if not visuals:
        return ""
    roman = ["I","II","III","IV","V"]
    cards = ""
    for i, v in enumerate(visuals[:4]):
        vtype    = v.get("type","illustration")
        raw_title = v.get("title","")          # unescaped — used for SVG type matching
        title    = _e(raw_title)
        desc     = _e(v.get("description",""))
        helps    = _e(v.get("how_it_helps",""))
        terms    = [_e(s) for s in v.get("search_terms",[])[:3]]
        kw       = " &nbsp;&#183;&nbsp; ".join(terms) if terms else ""
        plate_svg = _vis_svg(vtype, raw_title, t['pri'], t['sec'], t['bg'])
        cards += f"""
<div class="plate-card">
  <div class="plate-img">{plate_svg}</div>
  <div class="plate-body">
    <p class="plate-num" style="color:{t['sec']}">PLATE&nbsp;{roman[i]}</p>
    <p class="plate-title" style="color:{t['pri']}">{title}</p>
    <p class="plate-desc">{desc}</p>
    <p class="plate-helps"><em>{helps}</em></p>
    {'<p class="plate-kw">'+kw+'</p>' if kw else ''}
  </div>
</div>"""
    return f"""
<section class="page" id="visuals">
  <div class="sec-header" style="background:{t['dk']}">
    <span class="sec-label">Illustrated Guide</span>
  </div>
  <div class="pi">
    <div class="plates-grid">{cards}</div>
    <div class="pn">{pn}</div>
  </div>
</section>"""


# ── TAKEAWAYS ─────────────────────────────────────────────────────────────────

def _takeaways_page(tks, t, pn):
    if not tks:
        return ""
    items = ""
    for i, tk in enumerate(tks):
        point = _e(tk.get("point",""))
        why   = _e(tk.get("why_important",""))
        items += f"""
<div class="tk-row">
  <div class="tk-num" style="background:{t['pri']};color:#fff">{i+1}</div>
  <div class="tk-body" style="border-left:4px solid {t['lt']}">
    <p class="tk-point">{point}</p>
    <p class="tk-why" style="color:{t['dk']}">{why}</p>
  </div>
</div>"""
    return f"""
<section class="page" id="takeaways">
  <div class="sec-header" style="background:{t['pri']}">
    <span class="sec-label">What to Remember</span>
  </div>
  <div class="pi">
    <div class="tk-list">{items}</div>
    <div class="pn">{pn}</div>
  </div>
</section>"""


# ── QUIZ ──────────────────────────────────────────────────────────────────────

def _quiz_page(questions, t, pn):
    if not questions:
        return ""
    cards = ""
    for qi, q in enumerate(questions):
        qtext   = _e(q.get("question",""))
        options = q.get("options",[])
        answer  = _e(q.get("answer","A"))
        expl    = _e(q.get("explanation",""))
        opts_html = ""
        for opt in options:
            letter = _e(opt[0]) if opt else ""
            text   = _e(opt[3:]) if len(opt) > 3 else _e(opt)
            opts_html += f"""<button class="qopt" data-q="{qi}" data-letter="{letter}" onclick="checkAnswer({qi},this,'{answer}')">
  <span class="q-letter" style="background:{t['lt']};color:{t['pri']}">{letter}</span>
  <span class="q-text">{text}</span>
</button>"""
        cards += f"""
<div class="q-card" id="qcard{qi}">
  <div class="q-header" style="background:{t['bg']}">
    <span class="q-badge" style="background:{t['pri']};color:#fff">Q{qi+1}</span>
    <p class="q-question">{qtext}</p>
  </div>
  <div class="q-options">{opts_html}</div>
  <div class="q-expl" id="qexpl{qi}" style="display:none;border-color:{t['pri']};background:{t['bg']}">
    <strong style="color:{t['pri']}">&#9989; Explanation: </strong>{expl}
  </div>
</div>"""
    return f"""
<section class="page" id="quiz">
  <div class="sec-header" style="background:{t['sec']}">
    <span class="sec-label">Test Yourself</span>
  </div>
  <div class="pi">
    <div class="q-list">{cards}</div>
    <div class="q-score-box" id="qscore" style="display:none;border-color:{t['pri']};background:{t['bg']}">
      <span id="qscoretext" style="color:{t['pri']}"></span>
    </div>
    <div class="pn">{pn}</div>
  </div>
</section>"""


# ── ARTICLE ───────────────────────────────────────────────────────────────────

def _article_page(title, body, t, pn):
    if not body:
        return ""
    return f"""
<section class="page" id="article">
  <div class="sec-header" style="background:{t['pri']}">
    <span class="sec-label">In Depth</span>
  </div>
  <div class="pi">
    <h2 class="art-title" style="color:{t['pri']}">{_e(title)}</h2>
    <div class="art-rule" style="background:linear-gradient(to right,{t['sec']},{t['lt']},transparent)"></div>
    <div class="artbody">{_md(body)}</div>
    <div class="pn">{pn}</div>
  </div>
</section>"""


# ── CLOSING ───────────────────────────────────────────────────────────────────

def _closing(tks, t):
    quote = (tks[0].get("point","") if tks else "") or "Every question you ask makes you a little wiser."
    return f"""
<section class="page closing-page" id="closing">
  <div class="closing-band" style="background:linear-gradient(135deg,{t['pri']},{t['dk']})">
    <div class="cl-stars">&#10022; &#10022; &#10022;</div>
    <span class="cl-qmark">"</span>
    <p class="cl-quote">{_e(quote)}</p>
    <div class="cl-divider"></div>
    <p class="cl-body">Keep questioning. Keep exploring. The more you learn, the more the world opens up to you.</p>
    <p class="cl-footer">Study Buddy AI &nbsp;&#183;&nbsp; Powered by Groq</p>
  </div>
</section>"""


# ── PUBLIC ENTRY POINT ────────────────────────────────────────────────────────

def render_book_html(state: dict) -> str:
    topic    = state.get("topic")   or "Study Topic"
    subject  = state.get("subject") or "General"
    concepts = list(state.get("key_concepts") or [])
    summary  = state.get("brief_summary") or ""
    facts    = [f for f in (state.get("did_you_know_facts")   or []) if isinstance(f, dict)]
    visuals  = [v for v in (state.get("visual_descriptions")  or []) if isinstance(v, dict)]
    tks      = [tk for tk in (state.get("key_takeaways")      or []) if isinstance(tk, dict)]
    quiz     = [q for q in (state.get("quiz_questions")       or []) if isinstance(q, dict)]
    a_title  = state.get("article_title")   or topic
    a_body   = state.get("article_content") or ""

    t        = _theme(subject)
    read_min = _rtime(state)

    pn    = 1
    parts = [_cover(topic, subject, concepts, read_min, t)]

    if summary or concepts:
        parts.append(_overview(summary, concepts, subject, t, pn)); pn += 1
    if facts:
        parts.append(_facts_page(facts, t, pn)); pn += 1
    if visuals:
        parts.append(_visuals_page(visuals, t, pn)); pn += 1
    if tks:
        parts.append(_takeaways_page(tks, t, pn)); pn += 1
    if quiz:
        parts.append(_quiz_page(quiz, t, pn)); pn += 1
    if a_body:
        parts.append(_article_page(a_title, a_body, t, pn)); pn += 1

    parts.append(_closing(tks, t))
    return _wrap("\n".join(parts), topic, t)


# ── HTML SHELL ────────────────────────────────────────────────────────────────

def _wrap(pages: str, topic: str, t: dict) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(topic)} — Study Buddy</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800;900&family=Nunito:wght@400;600;700;800&family=Playfair+Display:ital,wght@0,700;0,900;1,400&display=swap" rel="stylesheet">
<style>
/* ── RESET ── */
*{{margin:0;padding:0;box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}

/* ── ROOT ── */
:root{{
  --pri:{t['pri']}; --sec:{t['sec']}; --dk:{t['dk']};
  --bg:{t['bg']};   --lt:{t['lt']};
  --ink:#1a1a2e; --muted:#555; --white:#fff;
  --shadow:0 4px 20px rgba(0,0,0,.12);
}}

body{{
  font-family:'Nunito',Arial,sans-serif;
  background:#e8e8e8;
  background-image:radial-gradient(#ccc 1px,transparent 1px);
  background-size:24px 24px;
  color:var(--ink);
  min-height:100vh;
}}

/* ── NAV ── */
.topnav{{
  position:sticky;top:0;z-index:200;
  background:var(--dk);
  display:flex;align-items:center;
  padding:0 20px;height:50px;
  box-shadow:0 3px 16px rgba(0,0,0,.3);
  gap:4px;
}}
.nav-brand{{
  font-family:'Poppins',sans-serif;font-weight:800;font-size:16px;
  color:#fff;margin-right:auto;letter-spacing:.5px;
}}
.nav-links a{{
  color:rgba(255,255,255,.8);text-decoration:none;
  font-size:12px;font-weight:600;padding:5px 10px;border-radius:6px;
  transition:background .15s;white-space:nowrap;
}}
.nav-links a:hover{{background:rgba(255,255,255,.18);color:#fff}}
.nav-btn{{
  background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.28);
  color:#fff;padding:5px 11px;border-radius:7px;
  cursor:pointer;font-size:13px;margin-left:8px;
  font-family:'Nunito',sans-serif;font-weight:700;
  transition:background .15s;
}}
.nav-btn:hover{{background:rgba(255,255,255,.28)}}

/* ── PROGRESS ── */
#prog{{position:fixed;top:50px;left:0;height:4px;width:0;background:var(--sec);z-index:300;transition:width .1s}}

/* ── BOOK SHELL ── */
.book-outer{{max-width:860px;margin:0 auto;padding:28px 16px 80px}}

/* ── PAGE ── */
.page{{
  background:#fff;border-radius:6px;
  box-shadow:var(--shadow);
  margin-bottom:40px;overflow:hidden;
  opacity:0;transform:translateY(20px);
  animation:rise .6s ease forwards;
}}
.page:nth-child(1){{animation-delay:.05s}}
.page:nth-child(2){{animation-delay:.18s}}
.page:nth-child(3){{animation-delay:.32s}}
.page:nth-child(4){{animation-delay:.46s}}
.page:nth-child(5){{animation-delay:.60s}}
.page:nth-child(6){{animation-delay:.74s}}
.page:nth-child(7){{animation-delay:.88s}}
.page:nth-child(8){{animation-delay:1.0s}}
@keyframes rise{{to{{opacity:1;transform:translateY(0)}}}}

/* ── SECTION HEADER BAR ── */
.sec-header{{
  padding:14px 32px;
  display:flex;align-items:center;
}}
.sec-label{{
  font-family:'Poppins',sans-serif;font-weight:800;font-size:13px;
  letter-spacing:3px;text-transform:uppercase;color:#fff;
}}

/* ── PAGE INNER ── */
.pi{{padding:32px 40px 28px}}

/* ── PAGE NUMBER ── */
.pn{{
  text-align:right;font-size:12px;color:#bbb;
  margin-top:20px;font-weight:600;letter-spacing:1px;
}}

/* ═══════════════════════════════════════════════════════════
   COVER
═══════════════════════════════════════════════════════════ */
.cover-top{{
  text-align:center;padding:44px 40px 36px;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.subj-badge{{
  display:inline-block;
  background:rgba(255,255,255,.22);border:2px solid rgba(255,255,255,.55);
  color:#fff;font-family:'Poppins',sans-serif;font-weight:800;
  font-size:11px;letter-spacing:4px;text-transform:uppercase;
  padding:6px 20px;border-radius:40px;margin-bottom:28px;
}}
.cov-svg{{width:160px;height:140px;margin:0 auto 24px;display:flex;align-items:center;justify-content:center}}
.cov-svg svg{{width:100%;height:100%;filter:drop-shadow(0 6px 18px rgba(0,0,0,.25))}}
.cov-title{{
  font-family:'Poppins',sans-serif;font-weight:900;
  font-size:42px;line-height:1.1;color:#fff;
  text-shadow:0 2px 12px rgba(0,0,0,.25);margin-bottom:12px;
}}
.cov-meta{{
  color:rgba(255,255,255,.78);font-size:14px;font-weight:600;
  letter-spacing:1px;margin-bottom:0;
}}
.cover-bot{{
  padding:24px 40px 28px;background:#fff;
}}
.cov-intro{{
  font-size:16px;color:#555;line-height:1.7;margin-bottom:16px;text-align:center;
}}
.ctags{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}}
.ctag{{
  background:var(--bg);border:2px solid var(--lt);
  color:var(--dk);font-weight:700;font-size:13px;
  padding:5px 15px;border-radius:30px;
}}

/* ═══════════════════════════════════════════════════════════
   OVERVIEW
═══════════════════════════════════════════════════════════ */
.two-col{{display:grid;grid-template-columns:1fr 260px;gap:28px}}
.col-main{{}}
.col-side{{}}
.body-text{{font-size:16px;line-height:1.85;color:#333;margin-bottom:20px;overflow:hidden}}
.dropcap{{
  float:left;font-family:'Playfair Display',serif;font-weight:900;
  font-size:72px;line-height:.78;margin-right:8px;margin-top:6px;
  padding:4px 10px;border-radius:6px;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.pull-quote{{
  border-left:5px solid var(--sec);
  padding:16px 20px;border-radius:0 10px 10px 0;margin:20px 0;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.pq-mark{{font-family:'Playfair Display',serif;font-size:52px;line-height:.6;display:block;margin-bottom:4px}}
.pq-text{{font-size:16px;font-weight:600;line-height:1.6;font-style:italic}}
.side-label{{
  font-family:'Poppins',sans-serif;font-weight:800;font-size:10px;
  letter-spacing:3px;margin-bottom:12px;
}}
.concepts-list{{display:flex;flex-direction:column;gap:8px}}
.concept-card{{
  display:flex;align-items:center;gap:10px;
  padding:10px 14px;border-radius:8px;border:2px solid var(--lt);
  background:var(--bg);
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.cc-icon{{font-size:18px}}
.cc-name{{font-weight:700;font-size:14px;color:var(--ink)}}

/* ═══════════════════════════════════════════════════════════
   FACTS — 5 distinct card styles
═══════════════════════════════════════════════════════════ */
.facts-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}

/* shared badge */
.fc-badge{{
  display:inline-block;
  font-family:'Poppins',sans-serif;font-weight:800;font-size:9px;
  letter-spacing:2px;text-transform:uppercase;
  padding:4px 10px;border-radius:20px;margin-bottom:10px;
}}
.fc-b-white{{background:rgba(255,255,255,.28);color:#fff}}

/* ── Card 1: HERO (full-width gradient) ── */
.fc-hero{{
  grid-column:span 2;border-radius:14px;
  padding:28px 24px;display:flex;align-items:center;gap:20px;
  box-shadow:0 6px 24px rgba(0,0,0,.22);
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.fc-h-body{{flex:1;min-width:0}}
.fc-h-em{{font-size:68px;flex-shrink:0;line-height:1;text-align:right}}
.fc-h-fact{{
  font-family:'Poppins',sans-serif;font-weight:800;font-size:17px;
  line-height:1.5;color:#fff;margin-bottom:10px;
}}
.fc-h-wow{{font-size:13px;font-style:italic;color:rgba(255,255,255,.82);line-height:1.55;margin:0}}

/* ── Card 2: BIG NUMBER (colored left panel) ── */
.fc-numcard{{
  border-radius:14px;overflow:hidden;display:flex;
  box-shadow:0 2px 14px rgba(0,0,0,.1);
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.fc-numcol{{
  width:58px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.fc-bignum{{
  font-family:'Poppins',sans-serif;font-weight:900;font-size:26px;
  color:rgba(255,255,255,.92);writing-mode:vertical-lr;letter-spacing:2px;
}}
.fc-ncbody{{padding:18px 16px;background:#fff;flex:1}}
.fc-ncfact{{font-size:14px;font-weight:700;line-height:1.6;color:#1a1a2e;margin-bottom:8px}}
.fc-ncwow{{font-size:12px;font-style:italic;font-weight:700;line-height:1.5;margin:0}}

/* ── Card 3: EMOJI STAR (centered giant emoji) ── */
.fc-emcard{{
  border-radius:14px;padding:22px 16px 18px;text-align:center;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.fc-emicon{{font-size:54px;display:block;margin-bottom:10px;line-height:1}}
.fc-emfact{{font-size:14px;font-weight:700;color:#1a1a2e;line-height:1.6;margin-bottom:7px}}
.fc-emwow{{font-size:12px;font-style:italic;font-weight:700;line-height:1.5;margin:0}}

/* ── Card 4: QUOTE (decorative quote mark) ── */
.fc-qcard{{
  border-radius:0 14px 14px 0;padding:18px 20px 18px 18px;
  background:#fff;box-shadow:0 2px 14px rgba(0,0,0,.08);
  position:relative;overflow:hidden;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.fc-qdeco{{
  font-family:'Playfair Display',serif;font-size:110px;line-height:.7;
  position:absolute;top:4px;left:8px;opacity:.1;font-weight:900;pointer-events:none;
}}
.fc-qbody{{position:relative;z-index:1}}
.fc-qfact{{font-size:14px;font-style:italic;font-weight:600;color:#1a1a2e;
  line-height:1.7;margin-bottom:8px}}
.fc-qwow{{font-size:12px;font-weight:700;line-height:1.5;margin:0}}

/* ── Card 5: SPOTLIGHT (accent bg, wow hero) ── */
.fc-spotlight{{
  border-radius:14px;padding:18px 20px;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.fc-sphead{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.fc-spem{{font-size:40px;line-height:1}}
.fc-spfact{{font-size:14px;font-weight:700;color:#1a1a2e;line-height:1.6;margin-bottom:8px}}
.fc-spwow{{font-size:16px;font-style:italic;font-weight:800;line-height:1.5;margin:0}}

/* ═══════════════════════════════════════════════════════════
   ILLUSTRATED GUIDE (Plates)
═══════════════════════════════════════════════════════════ */
.plates-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.plate-card{{
  border-radius:10px;overflow:hidden;
  box-shadow:0 2px 10px rgba(0,0,0,.09);
  border:1.5px solid var(--lt);
}}
.plate-img{{width:100%;height:130px;overflow:hidden;display:block}}
.plate-img svg{{width:100%;height:100%;display:block}}
.plate-body{{padding:14px 16px}}
.plate-num{{
  font-family:'Poppins',sans-serif;font-weight:800;font-size:10px;
  letter-spacing:3px;text-transform:uppercase;margin-bottom:4px;
}}
.plate-title{{font-weight:800;font-size:15px;margin-bottom:6px;line-height:1.3}}
.plate-desc{{font-size:13px;color:#444;line-height:1.6;margin-bottom:6px}}
.plate-helps{{font-size:12px;color:#666;line-height:1.5;margin-bottom:6px}}
.plate-kw{{font-size:11px;color:#888;font-weight:700;letter-spacing:.5px}}

/* ═══════════════════════════════════════════════════════════
   TAKEAWAYS
═══════════════════════════════════════════════════════════ */
.tk-list{{display:flex;flex-direction:column;gap:14px}}
.tk-row{{
  display:flex;align-items:flex-start;gap:16px;
  animation:slideIn .5s ease both;
}}
.tk-row:nth-child(1){{animation-delay:.1s}}
.tk-row:nth-child(2){{animation-delay:.2s}}
.tk-row:nth-child(3){{animation-delay:.3s}}
.tk-row:nth-child(4){{animation-delay:.4s}}
.tk-row:nth-child(5){{animation-delay:.5s}}
@keyframes slideIn{{from{{opacity:0;transform:translateX(-16px)}}to{{opacity:1;transform:none}}}}
.tk-num{{
  width:44px;height:44px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-family:'Poppins',sans-serif;font-weight:900;font-size:18px;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.tk-body{{
  flex:1;padding:14px 18px;border-radius:0 10px 10px 0;
  background:#fafafa;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.tk-point{{font-size:15px;font-weight:700;color:#1a1a2e;line-height:1.6;margin-bottom:5px}}
.tk-why{{font-size:13px;font-style:italic;line-height:1.5}}

/* ═══════════════════════════════════════════════════════════
   QUIZ
═══════════════════════════════════════════════════════════ */
.q-list{{display:flex;flex-direction:column;gap:20px}}
.q-card{{border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08)}}
.q-header{{padding:14px 18px;display:flex;align-items:flex-start;gap:14px}}
.q-badge{{
  flex-shrink:0;width:34px;height:34px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-family:'Poppins',sans-serif;font-weight:800;font-size:13px;
}}
.q-question{{font-weight:700;font-size:15px;line-height:1.55;padding-top:4px}}
.q-options{{padding:0 18px 14px;display:flex;flex-direction:column;gap:8px}}
.qopt{{
  display:flex;align-items:center;gap:12px;width:100%;
  border:2px solid #e0e0e0;border-radius:8px;padding:11px 14px;
  background:#fff;cursor:pointer;text-align:left;
  font-family:'Nunito',sans-serif;font-size:14px;font-weight:600;color:#333;
  transition:border-color .15s,background .15s;
}}
.qopt:hover{{border-color:var(--pri);background:var(--bg)}}
.qopt.correct{{background:#e8f5e9;border-color:#2e7d32;color:#1b5e20}}
.qopt.wrong  {{background:#ffebee;border-color:#c62828;color:#7f0000}}
.qopt.disabled{{cursor:default;pointer-events:none}}
.q-letter{{
  width:28px;height:28px;border-radius:6px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-family:'Poppins',sans-serif;font-weight:800;font-size:13px;
}}
.q-text{{flex:1}}
.q-expl{{
  margin:0 18px 14px;padding:12px 16px;border-radius:8px;border-left:4px solid;
  font-size:14px;line-height:1.6;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.q-score-box{{
  margin-top:18px;padding:16px 24px;border-radius:10px;border:3px solid;
  text-align:center;font-family:'Poppins',sans-serif;font-size:18px;font-weight:800;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}

/* ═══════════════════════════════════════════════════════════
   ARTICLE
═══════════════════════════════════════════════════════════ */
.art-title{{
  font-family:'Poppins',sans-serif;font-weight:900;font-size:26px;
  line-height:1.2;margin-bottom:14px;
}}
.art-rule{{height:4px;border-radius:2px;margin-bottom:24px;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
.artbody{{font-size:15.5px;line-height:1.9;color:#2a2a2a}}
.artbody .ah1{{font-family:'Poppins',sans-serif;font-weight:900;font-size:22px;
  margin:28px 0 10px;color:var(--pri)}}
.artbody .ah2{{font-family:'Poppins',sans-serif;font-weight:800;font-size:18px;
  margin:22px 0 8px;color:var(--pri);padding-bottom:6px;border-bottom:2px solid var(--lt)}}
.artbody .ah3{{font-family:'Poppins',sans-serif;font-weight:700;font-size:15px;
  margin:16px 0 6px;color:var(--dk);font-style:italic}}
.artbody .ap{{margin-bottom:18px}}
.artbody strong{{font-weight:800}}
.artbody em{{font-style:italic}}
.funfact{{
  background:var(--bg);border-left:5px solid var(--sec);
  padding:14px 18px;border-radius:0 8px 8px 0;margin:18px 0;
  font-weight:700;font-size:14px;line-height:1.6;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}

/* ═══════════════════════════════════════════════════════════
   CLOSING
═══════════════════════════════════════════════════════════ */
.closing-page{{overflow:hidden}}
.closing-band{{
  padding:60px 48px;text-align:center;
  -webkit-print-color-adjust:exact;print-color-adjust:exact;
}}
.cl-stars{{color:rgba(255,255,255,.5);font-size:20px;letter-spacing:10px;margin-bottom:16px}}
.cl-qmark{{font-family:'Playfair Display',serif;font-size:80px;line-height:.7;
  display:block;color:rgba(255,255,255,.5);margin-bottom:-8px}}
.cl-quote{{
  font-family:'Poppins',sans-serif;font-weight:800;font-size:24px;
  color:#fff;line-height:1.4;max-width:520px;margin:0 auto 28px;
}}
.cl-divider{{width:60px;height:3px;background:rgba(255,255,255,.4);margin:0 auto 24px;border-radius:2px}}
.cl-body{{color:rgba(255,255,255,.82);font-size:16px;line-height:1.75;
  max-width:440px;margin:0 auto 24px;font-style:italic}}
.cl-footer{{color:rgba(255,255,255,.45);font-size:11px;font-weight:700;
  letter-spacing:3px;text-transform:uppercase}}

/* ═══════════════════════════════════════════════════════════
   PRINT
═══════════════════════════════════════════════════════════ */
@media print{{
  body{{background:#fff}}
  .topnav,#prog{{display:none!important}}
  .book-outer{{padding:0;max-width:none}}
  .page{{
    margin-bottom:0;box-shadow:none;border-radius:0;
    break-after:page;opacity:1!important;transform:none!important;
    animation:none!important;
  }}
  .closing-page{{break-after:avoid}}
  .sec-header,.cover-top,.ctag,.dropcap,.pull-quote,.concept-card,
  .fc-hero,.fc-numcard,.fc-numcol,.fc-emcard,.fc-qcard,.fc-spotlight,
  .plate-img,.tk-num,.tk-body,.funfact,
  .closing-band,.q-header,.q-expl,.q-score-box{{
    -webkit-print-color-adjust:exact;print-color-adjust:exact;
  }}
  .tk-row,.fc-hero,.fc-numcard,.fc-emcard,.fc-qcard,.fc-spotlight,
  .q-card,.plate-card{{break-inside:avoid}}
  .facts-grid{{grid-template-columns:1fr 1fr}}
  .two-col{{grid-template-columns:1fr 220px}}
}}

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════ */
@media(max-width:640px){{
  .cov-title{{font-size:28px}}
  .two-col{{grid-template-columns:1fr}}
  .col-side{{order:-1}}
  .facts-grid{{grid-template-columns:1fr}}
  .fc-hero{{grid-column:span 1}}
  .plates-grid{{grid-template-columns:1fr}}
  .pi{{padding:20px 18px 16px}}
  .sec-header{{padding:12px 20px}}
  .nav-links{{display:none}}
}}
</style>
</head>
<body>

<nav class="topnav">
  <div class="nav-brand">&#128218; Study Buddy</div>
  <div class="nav-links">
    <a href="#cover">Cover</a>
    <a href="#overview">Overview</a>
    <a href="#facts">Facts</a>
    <a href="#visuals">Illustrations</a>
    <a href="#takeaways">Takeaways</a>
    <a href="#quiz">Quiz</a>
    <a href="#article">Article</a>
  </div>
  <button class="nav-btn" onclick="window.print()">&#128424; Print</button>
</nav>

<div id="prog"></div>
<div class="book-outer">{pages}</div>

<script>
window.addEventListener('scroll',()=>{{
  const d=document.documentElement;
  const pct=(d.scrollTop/(d.scrollHeight-d.clientHeight))*100;
  document.getElementById('prog').style.width=Math.min(pct,100)+'%';
}});
document.querySelectorAll('.topnav a').forEach(a=>{{
  a.addEventListener('click',e=>{{
    e.preventDefault();
    const el=document.querySelector(a.getAttribute('href'));
    if(el)el.scrollIntoView({{behavior:'smooth'}});
  }});
}});
const _ans={{}};
function checkAnswer(qi,btn,correct){{
  if(_ans[qi])return;
  _ans[qi]=true;
  const card=document.getElementById('qcard'+qi);
  card.querySelectorAll('.qopt').forEach(b=>{{
    b.classList.add('disabled');
    if(b.dataset.letter===correct)b.classList.add('correct');
    else if(b===btn)b.classList.add('wrong');
  }});
  const ex=document.getElementById('qexpl'+qi);
  if(ex)ex.style.display='block';
  const total=document.querySelectorAll('.q-card').length;
  if(Object.keys(_ans).length===total){{
    const ok=document.querySelectorAll('.qopt.correct.disabled').length;
    const box=document.getElementById('qscore');
    box.style.display='block';
    document.getElementById('qscoretext').textContent=
      '&#127942; Score: '+ok+' / '+total+
      (ok===total?' — Perfect! &#127881;':ok>=total/2?' — Well done! &#128077;':' — Keep practising! &#128170;');
  }}
}}
</script>
</body>
</html>"""
