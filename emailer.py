import logging
import os
import random
import re
import smtplib
import textwrap
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ── Category metadata ──────────────────────────────────────────────────────────

CATEGORY_META = {
    "competitive_intelligence": ("Competitive Intel", "#ffe8e8", "#c00"),
    "partner_signals":          ("Partner Signal",   "#e8f5e9", "#2e7d32"),
    "advertiser_trends":        ("Advertiser Trend", "#e8f0fe", "#1a56db"),
    "social_media":             ("Social Media",     "#fce4ec", "#880e4f"),
    "uk_market":                ("UK Market",        "#e2e8f0", "#374151"),
    "policy_regulation":        ("Policy",           "#f3e5f5", "#6a1b9a"),
    "industry_trends":          ("Industry",         "#e0f7fa", "#006064"),
}

BU_META = {
    "Platform Partnerships": ("#6a1b9a", "#fff"),
}

COMPETITOR_LABELS = {
    "mntn":    "MNTN",
    "vibe_co": "Vibe.co",
    "tatari":  "Tatari",
    "roku":    "Roku",
    "amazon":  "Amazon",
    "nbcu":    "NBCU",
}

# ── Daily trivia questions ─────────────────────────────────────────────────────
# 60 questions: 12 each for Geography, History, Science, Sports, Entertainment

TRIVIA_QUESTIONS: list[dict] = [
    # ── Geography ──
    {"topic": "Geography", "question": "What is the capital city of Australia?", "answer": "Canberra"},
    {"topic": "Geography", "question": "Which river is the longest in Africa?", "answer": "The Nile"},
    {"topic": "Geography", "question": "What country contains the most natural lakes in the world?", "answer": "Canada"},
    {"topic": "Geography", "question": "In which South American country is the Atacama Desert located?", "answer": "Chile"},
    {"topic": "Geography", "question": "What is the smallest country in the world by land area?", "answer": "Vatican City"},
    {"topic": "Geography", "question": "Which two countries share the longest international land border?", "answer": "Canada and the United States"},
    {"topic": "Geography", "question": "What is the deepest lake in the world?", "answer": "Lake Baikal (Russia)"},
    {"topic": "Geography", "question": "Which country actually has more ancient pyramids than Egypt?", "answer": "Sudan"},
    {"topic": "Geography", "question": "The Strait of Malacca separates the Malay Peninsula from which large island?", "answer": "Sumatra"},
    {"topic": "Geography", "question": "Which mountain range is traditionally considered the boundary between Europe and Asia?", "answer": "The Ural Mountains"},
    {"topic": "Geography", "question": "What is the only sea with no coastline, surrounded entirely by ocean water?", "answer": "The Sargasso Sea"},
    {"topic": "Geography", "question": "Which African country has the largest land area?", "answer": "Algeria"},
    # ── History ──
    {"topic": "History", "question": "In what year did the Berlin Wall fall?", "answer": "1989"},
    {"topic": "History", "question": "Who was the first woman to win a Nobel Prize?", "answer": "Marie Curie (1903, Physics)"},
    {"topic": "History", "question": "What was the name of the empire ruled by Genghis Khan?", "answer": "The Mongol Empire"},
    {"topic": "History", "question": "In what year did World War I begin?", "answer": "1914"},
    {"topic": "History", "question": "Which country was the first in the world to grant women the right to vote nationally?", "answer": "New Zealand (1893)"},
    {"topic": "History", "question": "The Battle of Waterloo in 1815 ended the rule of which European leader?", "answer": "Napoleon Bonaparte"},
    {"topic": "History", "question": "In what year did the Soviet Union officially dissolve?", "answer": "1991"},
    {"topic": "History", "question": "Who was the first President of the United States?", "answer": "George Washington"},
    {"topic": "History", "question": "The Magna Carta, limiting royal power in England, was signed in what year?", "answer": "1215"},
    {"topic": "History", "question": "Which ancient wonder of the world stood at the entrance to the harbor of Rhodes?", "answer": "The Colossus of Rhodes"},
    {"topic": "History", "question": "What was the name of the ship that sank after striking an iceberg on April 14, 1912?", "answer": "RMS Titanic"},
    {"topic": "History", "question": "The Silk Road connected ancient China to which western endpoint, now in modern-day Turkey?", "answer": "Constantinople (Istanbul)"},
    # ── Science ──
    {"topic": "Science", "question": "What is the chemical symbol for gold on the periodic table?", "answer": "Au"},
    {"topic": "Science", "question": "How many bones are in the adult human body?", "answer": "206"},
    {"topic": "Science", "question": "What element has atomic number 1?", "answer": "Hydrogen"},
    {"topic": "Science", "question": "What is the term for the organelle known as 'the powerhouse of the cell'?", "answer": "Mitochondria"},
    {"topic": "Science", "question": "How many chromosomes do humans normally have?", "answer": "46"},
    {"topic": "Science", "question": "What gas do plants absorb from the atmosphere during photosynthesis?", "answer": "Carbon dioxide (CO₂)"},
    {"topic": "Science", "question": "What is the hardest natural substance on Earth?", "answer": "Diamond"},
    {"topic": "Science", "question": "In which organ of the body is insulin produced?", "answer": "The pancreas"},
    {"topic": "Science", "question": "What is the most abundant gas in Earth's atmosphere?", "answer": "Nitrogen (about 78%)"},
    {"topic": "Science", "question": "What is the name of the force that keeps planets in orbit around the sun?", "answer": "Gravity"},
    {"topic": "Science", "question": "What is the speed of light in a vacuum, to the nearest whole number in millions of meters per second?", "answer": "300 million meters per second (299,792,458 m/s)"},
    {"topic": "Science", "question": "What is the term for a scientist who studies earthquakes?", "answer": "Seismologist"},
    # ── Sports ──
    {"topic": "Sports", "question": "How many rings appear on the Olympic flag?", "answer": "Five"},
    {"topic": "Sports", "question": "In tennis, what is the term for a score of 40–40?", "answer": "Deuce"},
    {"topic": "Sports", "question": "Which country has won the most FIFA World Cup titles?", "answer": "Brazil (5 titles)"},
    {"topic": "Sports", "question": "How many players from each team are on the court at one time in basketball?", "answer": "Five"},
    {"topic": "Sports", "question": "In golf, what is the term for completing a hole one stroke under par?", "answer": "Birdie"},
    {"topic": "Sports", "question": "How long is each end zone in American football, in yards?", "answer": "10 yards"},
    {"topic": "Sports", "question": "In which sport would you perform a butterfly stroke?", "answer": "Swimming"},
    {"topic": "Sports", "question": "What is the maximum score achievable in a single game of ten-pin bowling?", "answer": "300"},
    {"topic": "Sports", "question": "How many balls does a batter need to receive for a walk in baseball?", "answer": "Four"},
    {"topic": "Sports", "question": "The Stanley Cup is the championship trophy for which professional sport?", "answer": "Ice hockey (NHL)"},
    {"topic": "Sports", "question": "In what country did the sport of rugby originate?", "answer": "England"},
    {"topic": "Sports", "question": "What is the diameter of a regulation basketball hoop in inches?", "answer": "18 inches"},
    # ── Entertainment ──
    {"topic": "Entertainment", "question": "Who directed the 1975 blockbuster film Jaws?", "answer": "Steven Spielberg"},
    {"topic": "Entertainment", "question": "Which Shakespeare play features the characters Rosencrantz and Guildenstern?", "answer": "Hamlet"},
    {"topic": "Entertainment", "question": "Which artist painted the ceiling of the Sistine Chapel?", "answer": "Michelangelo"},
    {"topic": "Entertainment", "question": "What fictional paper company is at the center of the TV show The Office?", "answer": "Dunder Mifflin"},
    {"topic": "Entertainment", "question": "What band was Freddie Mercury the lead singer of?", "answer": "Queen"},
    {"topic": "Entertainment", "question": "Who wrote the Harry Potter book series?", "answer": "J.K. Rowling"},
    {"topic": "Entertainment", "question": "In which US city is the TV show Seinfeld set?", "answer": "New York City"},
    {"topic": "Entertainment", "question": "What musician is known as 'The King of Pop'?", "answer": "Michael Jackson"},
    {"topic": "Entertainment", "question": "The TV show Breaking Bad is set primarily in which US city?", "answer": "Albuquerque, New Mexico"},
    {"topic": "Entertainment", "question": "What 1994 film starring Tom Hanks follows a slow-witted man who witnesses major historical events?", "answer": "Forrest Gump"},
    {"topic": "Entertainment", "question": "Which novel by F. Scott Fitzgerald is set in the fictional Long Island towns of East Egg and West Egg?", "answer": "The Great Gatsby"},
    {"topic": "Entertainment", "question": "What is the name of the fictional African kingdom in the 2018 Marvel film Black Panther?", "answer": "Wakanda"},
]

# ── Shared style values ────────────────────────────────────────────────────────

_FONT = "'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"
_TEXT = f"font-family:{_FONT};color:#1a202c"

# ── HTML helpers ───────────────────────────────────────────────────────────────

def _cap_sentences(text: str, n: int) -> str:
    parts = re.split(r'(?<=[.!?])\s+', text.strip(), maxsplit=n)
    return ' '.join(parts[:n])


def _tag_html(categories: list[str]) -> str:
    parts = []
    for cat in categories:
        label, bg, fg = CATEGORY_META.get(cat, (cat.replace("_", " ").title(), "#edf2f7", "#4a5568"))
        parts.append(
            f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
            f'font-size:10px;font-weight:600;margin-right:3px;'
            f'background:{bg};color:{fg}">{label}</span>'
        )
    return "".join(parts)


def _region_tags_html(regions: list[str]) -> str:
    return "".join(
        f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
        f'font-size:10px;font-weight:600;margin-right:3px;'
        f'background:#374151;color:#fff">{r}</span>'
        for r in regions
    )


def _bu_tags_html(business_units: list[str]) -> str:
    parts = []
    for bu in business_units:
        bg, fg = BU_META.get(bu, ("#4a5568", "#fff"))
        parts.append(
            f'<span style="display:inline-block;padding:1px 6px;border-radius:3px;'
            f'font-size:10px;font-weight:600;margin-right:3px;'
            f'background:{bg};color:{fg}">{bu}</span>'
        )
    return "".join(parts)


def _score_badge(score: int) -> str:
    bg = {5: "#c00", 4: "#e65100"}.get(score, "#003087")
    return (
        f'<span style="display:inline-block;width:16px;height:16px;border-radius:50%;'
        f'font-size:9px;font-weight:800;text-align:center;line-height:16px;'
        f'margin-right:5px;vertical-align:middle;background:{bg};color:#fff">{score}</span>'
    )


def _source_link(url: str) -> str:
    if not url:
        return ""
    return f' <a href="{url}" style="font-size:11px;color:#003087;text-decoration:none">[source]</a>'


def _story_html(story: dict, is_last: bool = False) -> str:
    score = story.get("relevance_score", 3)
    title = story.get("title", "Untitled")
    url = story.get("url", "#")
    source = story.get("source", "")
    pub = story.get("published", "")
    summary = _cap_sentences(story.get("summary", ""), 2)
    impl = _cap_sentences(story.get("ua_implications", ""), 1)
    cats    = story.get("categories", [])
    bus     = story.get("business_units", [])
    regions = story.get("regions", [])

    title_color = "#c00" if score >= 5 else "#1a202c"
    link_color  = "#c00" if score >= 5 else "#003087"
    row_border  = "none" if is_last else "1px solid #f7fafc"

    impl_html = ""
    if impl:
        impl_html = (
            f'<div style="background:#fef9e7;border:1px solid #f6d860;border-radius:4px;'
            f'padding:6px 10px;margin-top:6px;font-size:12px;color:#5a4400;line-height:1.4;'
            f'font-family:{_FONT}">'
            f'<b style="color:#b8860b">UA Signal:</b> {impl}</div>'
        )

    all_tags = _tag_html(cats) + _bu_tags_html(bus) + _region_tags_html(regions)

    return (
        f'<div style="padding:10px 32px;border-bottom:{row_border}">'
        f'<div style="font-size:14px;font-weight:600;line-height:1.3;color:{title_color};'
        f'font-family:{_FONT}">'
        f'{_score_badge(score)}'
        f'<a href="{url}" style="color:{link_color};text-decoration:none">{title}</a>'
        f'</div>'
        f'<div style="color:#8895a7;font-size:11px;margin-top:2px;font-family:{_FONT}">'
        f'{source} &bull; {pub}</div>'
        f'<div style="margin-top:4px">{all_tags}</div>'
        f'<div style="font-size:13px;line-height:1.45;margin-top:5px;color:#3d4852;'
        f'font-family:{_FONT}">{summary}</div>'
        f'{impl_html}'
        f'</div>'
    )


def _section_wrap(heading: str, body: str) -> str:
    return (
        f'<div style="background:#fff;margin-top:8px">'
        f'<div style="padding:9px 32px;border-bottom:1px solid #edf2f7">'
        f'<h2 style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
        f'color:#003087;font-weight:700;font-family:{_FONT}">{heading}</h2>'
        f'</div>'
        f'{body}'
        f'</div>'
    )


def _comp_intel_html(comp: dict) -> str:
    sections = []

    landscape = comp.get("landscape", "")
    if landscape:
        sections.append(
            f'<div style="font-size:12px;color:#6b7280;line-height:1.5;'
            f'margin-bottom:10px;padding:8px 10px;background:#fafafa;'
            f'border-radius:4px;font-family:{_FONT}">'
            f'<span style="font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:.5px;margin-right:6px">Landscape</span>'
            f'{landscape}</div>'
        )

    for key, label in COMPETITOR_LABELS.items():
        items = comp.get(key, [])
        if not items:
            continue
        name_html = (
            f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.4px;color:#c00;margin:10px 0 3px;font-family:{_FONT}">'
            f'{label}</div>'
        )
        rows = ""
        for i in items:
            badge_html = ""
            tags = _bu_tags_html(i.get("business_units", [])) + _region_tags_html(i.get("regions", []))
            if tags:
                badge_html = f'<div style="margin-top:3px">{tags}</div>'
            rows += (
                f'<div style="font-size:13px;color:#3d4852;line-height:1.4;'
                f'padding-left:8px;border-left:2px solid #ffd0d0;margin-bottom:4px;'
                f'font-family:{_FONT}">'
                f'{i.get("insight","")}{_source_link(i.get("url",""))}{badge_html}</div>'
            )
        sections.append(name_html + rows)

    if not sections:
        return (
            f'<p style="padding:12px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No direct competitor mentions today.</p>'
        )
    return f'<div style="padding:2px 32px 10px">{"".join(sections)}</div>'


def _ua_partners_section(items: list[dict]) -> str:
    header = (
        f'<div style="background:#0d1b4b;padding:9px 32px">'
        f'<h2 style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
        f'color:#fff;font-weight:700;font-family:{_FONT}">UA Partners in the News</h2>'
        f'</div>'
    )
    if not items:
        return (
            f'<div style="background:#fff;margin-top:8px">'
            f'{header}'
            f'<p style="padding:12px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No partner news today.</p>'
            f'</div>'
        )

    rows = ""
    for idx, item in enumerate(items):
        partner  = item.get("partner", "")
        headline = item.get("headline", "")
        insight  = item.get("insight", "")
        url      = item.get("url", "")
        border   = "none" if idx == len(items) - 1 else "1px solid #f0f4ff"

        label = (
            f'<span style="display:inline-block;padding:2px 7px;border-radius:3px;'
            f'font-size:10px;font-weight:700;background:#1e3a8a;color:#fff;'
            f'text-transform:uppercase;letter-spacing:.3px;margin-right:8px;'
            f'vertical-align:middle;font-family:{_FONT}">{partner}</span>'
        )
        hed = (
            f'<a href="{url}" style="font-size:13px;font-weight:600;color:#1a202c;'
            f'text-decoration:none;vertical-align:middle;font-family:{_FONT}">{headline}</a>'
            if url else
            f'<span style="font-size:13px;font-weight:600;color:#1a202c;'
            f'vertical-align:middle;font-family:{_FONT}">{headline}</span>'
        )
        insight_html = (
            f'<div style="font-size:12px;color:#6b7280;line-height:1.4;'
            f'margin-top:5px;font-family:{_FONT}">'
            f'<span style="font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:.4px;margin-right:5px">Partnership signal:</span>'
            f'{insight}</div>'
        ) if insight else ""

        rows += (
            f'<div style="padding:10px 32px;border-bottom:{border}">'
            f'<div style="line-height:1.5">{label}{hed}</div>'
            f'{insight_html}'
            f'</div>'
        )

    return f'<div style="background:#fff;margin-top:8px">{header}{rows}</div>'


def _insight_list_html(items: list[dict]) -> str:
    if not items:
        return (
            f'<p style="padding:10px 32px 14px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'Nothing notable today.</p>'
        )
    rows = []
    for idx, i in enumerate(items):
        is_last = idx == len(items) - 1
        border = "none" if is_last else "1px solid #f7fafc"
        tags = _bu_tags_html(i.get("business_units", [])) + _region_tags_html(i.get("regions", []))
        badge_html = f'<div style="margin-top:3px">{tags}</div>' if tags else ""
        rows.append(
            f'<div style="font-size:13px;color:#3d4852;line-height:1.4;'
            f'padding:5px 0;border-bottom:{border};font-family:{_FONT}">'
            f'{i.get("insight","")}{_source_link(i.get("url",""))}{badge_html}</div>'
        )
    return f'<div style="padding:6px 32px 10px">{"".join(rows)}</div>'


def _finance_corner_html(items: list[dict]) -> str:
    if not items:
        return (
            f'<p style="padding:12px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No earnings or financial news today.</p>'
        )
    rows = ""
    for idx, item in enumerate(items[:4]):
        row_bg = "#fff" if idx % 2 == 0 else "#e8f5e9"
        url = item.get("url", "")
        headline = item.get("headline", "")
        metric = item.get("metric", "")
        headline_html = (
            f'<a href="{url}" style="color:#1b5e20;text-decoration:none;font-size:12px;'
            f'font-weight:600;line-height:1.4;font-family:{_FONT}">{headline}</a>'
            if url else
            f'<span style="font-size:12px;font-weight:600;color:#3d4852;font-family:{_FONT}">{headline}</span>'
        )
        metric_html = (
            f'<div style="font-size:11px;color:#8895a7;margin-top:2px;font-family:{_FONT}">{metric}</div>'
            if metric else ""
        )
        rows += (
            f'<tr style="background:{row_bg}">'
            f'<td style="padding:5px 8px;border:1px solid #c8e6c9;font-size:12px;font-weight:700;'
            f'color:#1b5e20;white-space:nowrap;vertical-align:top;font-family:{_FONT}">'
            f'{item.get("company","")}</td>'
            f'<td style="padding:5px 8px;border:1px solid #c8e6c9;vertical-align:top">'
            f'{headline_html}{metric_html}</td>'
            f'</tr>'
        )
    table = (
        f'<div style="padding:8px 32px 12px">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:#1b5e20">'
        f'<th style="padding:5px 8px;text-align:left;font-size:11px;font-weight:700;'
        f'color:#fff;font-family:{_FONT};border:1px solid #1b5e20;white-space:nowrap">Company</th>'
        f'<th style="padding:5px 8px;text-align:left;font-size:11px;font-weight:700;'
        f'color:#fff;font-family:{_FONT};border:1px solid #1b5e20">Headline &amp; Key Metric</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )
    return table


def _finance_corner_section(items: list[dict]) -> str:
    body = _finance_corner_html(items)
    return (
        f'<div style="background:#f1f8e9;margin-top:8px">'
        f'<div style="padding:9px 32px;border-bottom:1px solid #c8e6c9;background:#1b5e20">'
        f'<h2 style="margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;'
        f'color:#fff;font-weight:700;font-family:{_FONT}">Melissa&#8217;s Finance Corner &#128200;</h2>'
        f'</div>'
        f'{body}'
        f'</div>'
    )


def build_html(briefing: dict, article_count: int, run_date: str, sources: list[str]) -> str:
    _today = datetime.now().date()
    _rng = random.Random(_today.toordinal())
    trivia = _rng.choice(TRIVIA_QUESTIONS)
    trivia_inner = (
        f'<div style="color:#f07030;font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.6px;margin-bottom:7px;font-family:{_FONT}">{trivia["topic"]}</div>'
        f'<p style="font-style:italic;color:#e2e8f0;font-size:13px;line-height:1.65;'
        f'margin:0;font-weight:400;font-family:{_FONT}">{trivia["question"]}</p>'
    )
    trivia_answer_block = (
        f'<div style="background:#f7f7f7;border-top:1px solid #e2e8f0;'
        f'padding:10px 32px 12px;margin-top:8px">'
        f'<span style="color:#f07030;font-size:11px;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:.4px;font-family:{_FONT}">Trivia Answer: </span>'
        f'<span style="color:#6b7280;font-size:13px;font-family:{_FONT}">{trivia["answer"]}</span>'
        f'</div>'
    )
    exec_summary = briefing.get("executive_summary", "No summary available.")
    key_themes   = briefing.get("key_themes", [])
    top_stories  = briefing.get("top_stories", [])

    # ── Stories ──
    if top_stories:
        stories_html = "".join(
            _story_html(s, is_last=(idx == len(top_stories) - 1))
            for idx, s in enumerate(top_stories)
        )
    else:
        stories_html = (
            f'<p style="padding:16px 32px;color:#8895a7;font-size:13px;font-family:{_FONT}">'
            f'No highly-relevant stories today.</p>'
        )

    # ── Key themes list ──
    themes_html = "".join(
        f'<li style="font-family:{_FONT}">{t}</li>'
        for t in key_themes
    )

    # ── Other insight sections ──
    other_sections = ""
    for key, heading in [
        ("partner_signals",   "Partner &amp; Integration Signals"),
        ("advertiser_trends", "Advertiser Trends"),
        ("social_media",      "Meanwhile, in Social Media&#8230;"),
        ("uk_market",         "UK Market"),
    ]:
        items = briefing.get(key, [])
        if items:
            other_sections += _section_wrap(heading, _insight_list_html(items))

    # ── Policy compact block ──
    policy_items = briefing.get("policy_regulation", [])
    if policy_items:
        notes = " &bull; ".join(_cap_sentences(i.get("insight", ""), 1) for i in policy_items)
        policy_block = (
            f'<div style="background:#fff;padding:10px 32px 14px;font-size:12px;'
            f'color:#6b7280;line-height:1.55;margin-top:8px;font-family:{_FONT}">'
            f'<span style="font-weight:700;color:#9ca3af;text-transform:uppercase;'
            f'font-size:10px;letter-spacing:.5px;margin-right:5px">Policy notes:</span>'
            f'{notes}</div>'
        )
    else:
        policy_block = ""

    source_str = " &bull; ".join(sources)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Universal Ads Intelligence Brief &#8212; {run_date}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:{_FONT};color:#1a202c">
<div style="max-width:680px;margin:0 auto">

  <!-- Header -->
  <div style="background:#0a0a0f;padding:22px 32px 16px">
    <h1 style="color:#fff;margin:0;font-size:30px;font-weight:800;letter-spacing:-.5px;font-family:{_FONT}">Universal Ads</h1>
    <div style="height:4px;background:linear-gradient(90deg,#e8402a 0%,#f07030 50%,#4a7fd4 100%);border-radius:3px;margin:10px 0 9px"></div>
    <div style="color:#9ca3af;font-size:13px;font-weight:400;margin:0 0 5px;font-family:{_FONT}">Daily Intelligence Briefing</div>
    <div style="color:#6b7280;font-size:12px;margin-top:4px;font-family:{_FONT}">{run_date} &bull; {article_count} articles analyzed</div>
  </div>

  <!-- Daily trivia question -->
  <div style="background:#1a1a2e;padding:16px 32px 14px">
    {trivia_inner}
  </div>

  <!-- Executive summary -->
  <div style="background:#fff;border-left:4px solid #003087;padding:14px 32px">
    <p style="font-size:14px;font-weight:600;color:#003087;margin:0 0 6px;font-family:{_FONT}">Today&#8217;s Briefing</p>
    <p style="margin:0 0 8px;font-size:13px;line-height:1.5;color:#3d4852;font-family:{_FONT}">{exec_summary}</p>
    <div style="font-size:12px;font-weight:700;color:#5a6472;text-transform:uppercase;letter-spacing:.5px;font-family:{_FONT}">Key Themes</div>
    <ul style="margin:3px 0 0;padding-left:16px;font-size:13px;line-height:1.65;color:#3d4852">{themes_html}</ul>
  </div>

  <!-- Top Stories -->
  {_section_wrap("Top Stories", stories_html)}

  <!-- Competitive Intelligence -->
  {_section_wrap("Competitive Intelligence Detail",
    _comp_intel_html(briefing.get("competitive_intel", {}))
  )}

  <!-- UA Partners in the News -->
  {_ua_partners_section(briefing.get("ua_partners", []))}

  <!-- Finance Corner -->
  {_finance_corner_section(briefing.get("finance_corner", []))}

  <!-- Other sections: Partner, Advertiser, Social, UK Market -->
  {other_sections}

  <!-- Policy notes -->
  {policy_block}

  <!-- Trivia answer -->
  {trivia_answer_block}

  <!-- Footer -->
  <div style="background:#edf2f7;padding:10px 32px;font-size:11px;color:#8895a7;text-align:center;margin-top:8px;font-family:{_FONT}">
    Universal Ads Intelligence Brief &bull; Powered by Claude AI ({run_date})<br>
    Sources monitored: {source_str}
  </div>

</div>
</body>
</html>"""


def build_plaintext(briefing: dict, run_date: str) -> str:
    lines = [
        f"UNIVERSAL ADS INTELLIGENCE BRIEF — {run_date}",
        "=" * 60,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        briefing.get("executive_summary", ""),
        "",
        "KEY THEMES",
        "-" * 40,
    ]
    for t in briefing.get("key_themes", []):
        lines.append(f"• {t}")
    lines += ["", "TOP STORIES", "-" * 40]
    for s in briefing.get("top_stories", []):
        lines += [
            f"[{s.get('relevance_score',0)}/5] {s.get('title','')}",
            f"  {s.get('source','')} | {s.get('published','')}",
            f"  {s.get('url','')}",
            f"  {s.get('summary','')}",
            f"  UA Signal: {s.get('ua_implications','')}",
            "",
        ]
    return "\n".join(lines)


# ── Sending ────────────────────────────────────────────────────────────────────

_PRIMARY_RECIPIENT = "greglieber@gmail.com"


def send_briefing(briefing: dict, article_count: int) -> None:
    gmail_addr = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipients_raw = os.environ.get("RECIPIENT_EMAILS", gmail_addr)
    all_recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    sender_name = os.environ.get("SENDER_NAME", "Universal Ads Intelligence")

    # Primary recipient always goes in To; everyone else goes in Bcc
    bcc = [r for r in all_recipients if r.lower() != _PRIMARY_RECIPIENT]

    run_date = datetime.now().strftime("%A, %B %-d, %Y")
    subject = f"Universal Ads Intel Brief — {datetime.now().strftime('%b %-d, %Y')}"

    from config import RSS_FEEDS
    sources = list(RSS_FEEDS.keys())

    html_body = build_html(briefing, article_count, run_date, sources)
    text_body = build_plaintext(briefing, run_date)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{gmail_addr}>"
    msg["To"] = _PRIMARY_RECIPIENT
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    smtp_recipients = [_PRIMARY_RECIPIENT] + bcc
    logger.info(f"  To: {_PRIMARY_RECIPIENT}" + (f"  Bcc: {', '.join(bcc)}" if bcc else ""))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_addr, app_password)
        server.sendmail(gmail_addr, smtp_recipients, msg.as_string())
    logger.info("  Email sent successfully")
