import logging
import os
import random
import re
import smtplib
import textwrap
from datetime import date, datetime
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

# ── Stoic quotes ──────────────────────────────────────────────────────────────

STOIC_QUOTES: list[tuple[str, str]] = [
    # Marcus Aurelius — Meditations
    ("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    ("You have power over your mind, not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("The soul becomes dyed with the color of its thoughts.", "Marcus Aurelius"),
    ("If it is not right, do not do it; if it is not true, do not say it.", "Marcus Aurelius"),
    ("You could leave life right now. Let that determine what you do and say and think.", "Marcus Aurelius"),
    ("Very little is needed to make a happy life; it is all within yourself, in your way of thinking.", "Marcus Aurelius"),
    ("Accept the things to which fate binds you, and love the people with whom fate brings you together.", "Marcus Aurelius"),
    ("The best revenge is to be unlike him who performed the injury.", "Marcus Aurelius"),
    ("It is not death that a man should fear, but he should fear never beginning to live.", "Marcus Aurelius"),
    ("Loss is nothing else but change, and change is Nature's delight.", "Marcus Aurelius"),
    ("The first rule is to keep an untroubled spirit. The second is to look things in the face and know them for what they are.", "Marcus Aurelius"),
    ("Never esteem anything as of advantage to you that will make you break your word or lose your self-respect.", "Marcus Aurelius"),
    ("Do not act as if you had ten thousand years to live.", "Marcus Aurelius"),
    ("How much more grievous are the consequences of anger than the causes of it.", "Marcus Aurelius"),
    ("Confine yourself to the present.", "Marcus Aurelius"),
    ("Dwell on the beauty of life. Watch the stars, and see yourself running with them.", "Marcus Aurelius"),
    ("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    ("When you wake up in the morning, think of what a precious privilege it is to be alive — to breathe, to think, to enjoy, to love.", "Marcus Aurelius"),
    ("Everything we hear is an opinion, not a fact. Everything we see is a perspective, not the truth.", "Marcus Aurelius"),
    # Epictetus — Enchiridion & Discourses
    ("Make the best use of what is in your power, and take the rest as it happens.", "Epictetus"),
    ("Men are disturbed not by things, but by the opinions about things.", "Epictetus"),
    ("Seek not the good in external things; seek it in yourself.", "Epictetus"),
    ("No man is free who is not master of himself.", "Epictetus"),
    ("Don't explain your philosophy. Embody it.", "Epictetus"),
    ("First say to yourself what you would be; then do what you have to do.", "Epictetus"),
    ("Wealth consists not in having great possessions, but in having few wants.", "Epictetus"),
    ("If you want to improve, be content to be thought foolish and stupid.", "Epictetus"),
    ("The more we value things outside our control, the less control we have.", "Epictetus"),
    ("Seek not that the things which happen should happen as you wish; but wish the things which happen to be as they are, and you will have a tranquil flow of life.", "Epictetus"),
    ("He is a wise man who does not grieve for the things which he has not, but rejoices for those which he has.", "Epictetus"),
    ("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    ("Freedom is the only worthy goal in life. It is won by disregarding things that lie beyond our control.", "Epictetus"),
    ("Circumstances don't make the man, they only reveal him to himself.", "Epictetus"),
    ("We have two ears and one mouth so that we can listen twice as much as we speak.", "Epictetus"),
    # Seneca — Letters to Lucilius & Essays
    ("We suffer more in imagination than in reality.", "Seneca"),
    ("Begin at once to live, and count each separate day as a separate life.", "Seneca"),
    ("The whole future lies in uncertainty: live immediately.", "Seneca"),
    ("As long as you live, keep learning how to live.", "Seneca"),
    ("It is not the man who has too little, but the man who craves more, that is poor.", "Seneca"),
    ("While we wait for life, life passes.", "Seneca"),
    ("Omnia, Lucili, aliena sunt, tempus tantum nostrum est. — Everything is alien to us; time alone is ours.", "Seneca"),
    ("To be everywhere is to be nowhere.", "Seneca"),
    ("If you really want to escape the things that harass you, what you need is not to be in a different place but to be a different person.", "Seneca"),
    ("Associate with those who will make a better man of you. Welcome those whom you yourself can improve.", "Seneca"),
    ("The mind that is anxious about future events is miserable.", "Seneca"),
    ("He suffers more than necessary, who suffers before it is necessary.", "Seneca"),
    ("There is nothing the wise man does reluctantly. He escapes necessity because he wills what necessity will force upon him.", "Seneca"),
    ("Yield not to adversity; trust not to prosperity; keep before your eyes the full scope of Fortune's power.", "Seneca"),
    ("No wind favors him who has no destined port.", "Seneca"),
    ("He who is brave is free.", "Seneca"),
    # Zeno of Citium
    ("Man conquers the world by conquering himself.", "Zeno of Citium"),
    ("Better to stumble with the toe than with the tongue.", "Zeno of Citium"),
    ("Happiness is a good flow of life.", "Zeno of Citium"),
    ("All things are parts of one single system, which is called Nature.", "Zeno of Citium"),
    ("The goal of life is living in agreement with Nature.", "Zeno of Citium"),
    # Cato the Younger
    ("I begin to speak only when I'm certain what I'll say isn't better left unsaid.", "Cato the Younger"),
    ("Grasp the subject; the words will follow.", "Cato the Younger"),
    ("An angry man opens his mouth and shuts his eyes.", "Cato the Younger"),
    # Cleanthes
    ("Lead me, O Zeus, and lead me, Destiny, to that goal long ago assigned to me. I'll follow and not falter; if my will prove weak and craven, still I'll follow on.", "Cleanthes"),
    ("Seek not good from without; seek it from within yourselves, or you will never find it.", "Cleanthes"),
]

# ── Knicks fun facts — displayed May 27 through June 15, 2026 ─────────────────
# Index 0 = May 27, index 19 = June 15

KNICKS_FACTS: list[tuple[str, str]] = [
    # 0 — May 27
    (
        "On May 12, 1985, the NBA held its first-ever Draft Lottery — designed so all "
        "non-playoff teams had a shot at the top pick. The New York Knicks, fresh off a "
        "24-58 season, won. They used the selection on Georgetown center Patrick Ewing "
        "on June 18, 1985, and within three seasons turned into a perennial Eastern Conference "
        "force. Meanwhile, the Boston Celtics had won 63 games that year — and would spend "
        "the next decade watching Ewing torment them every spring.",
        "1985 NBA Draft Lottery",
    ),
    # 1 — May 28
    (
        "Patrick Ewing played 15 seasons as a Knick (1985–2000) and retired as the "
        "franchise's all-time leader in points (18,860), rebounds, blocked shots, and "
        "games played. He earned 11 All-Star selections in a Knicks uniform, was named "
        "to the NBA's 50 Greatest Players list in 1996, and guided New York to the "
        "playoffs in 13 of his 15 seasons. His No. 33 was retired in 2003 — the most "
        "decorated number in franchise history.",
        "Patrick Ewing Era, 1985–2000",
    ),
    # 2 — May 29
    (
        "Pat Riley's 1993–94 Knicks went 57-25 — the best record in the Eastern Conference "
        "— in a season defined by suffocating defense and collective will. With Michael Jordan "
        "retired, they bulldozed through New Jersey, outlasted the Chicago Bulls in seven games, "
        "and edged Indiana in seven more before losing to Hakeem Olajuwon's Houston Rockets "
        "in a seven-game Finals. The Knicks held opponents to fewer than 96 points per game, "
        "second-best in the league. It remains the franchise's last Finals appearance.",
        "1993–94 Knicks Season",
    ),
    # 3 — May 30
    (
        "Game 7 of the 1994 NBA Finals came down to 48 minutes in Houston. What stood "
        "between the Knicks and their second-ever championship: shooting guard John Starks "
        "went 2-for-18 from the field, 0-for-8 from three-point range, in the deciding game. "
        "Patrick Ewing scored 17 with 8 rebounds. The Knicks lost 90-84. Starks was so haunted "
        "by the performance that he produced a documentary about it 16 years later. Hakeem "
        "Olajuwon averaged 26.9 points and 9.1 rebounds for the series.",
        "1994 NBA Finals, Game 7",
    ),
    # 4 — May 31
    (
        "On May 16, 1999, with the Knicks trailing Miami 77-76 in Game 5 of the first "
        "round, Allan Houston drove the baseline with 4.5 seconds left. His running layup "
        "bounced off the front of the rim, rolled around slowly, and fell through with "
        "0.8 seconds remaining. Knicks 78, Heat 77. The shot — one of the most replayed "
        "in franchise history — eliminated the No. 1-seeded Heat and launched the "
        "Knicks on a run to the NBA Finals.",
        "May 16, 1999 — Allan Houston's Shot",
    ),
    # 5 — June 1
    (
        "The 1999 Knicks are still the only No. 8 seed in NBA history to reach the Finals. "
        "Playing in a lockout-shortened 50-game season, they finished 27-23, then eliminated "
        "the top-seeded Miami Heat, the Atlanta Hawks, and the No. 1 overall seed Indiana "
        "Pacers — going 11-4 in the postseason before losing to San Antonio 4-1 in the Finals. "
        "That same year, the Boston Celtics went 19-31 and didn't sniff the playoffs. "
        "Different franchises; different springs.",
        "1999 NBA Playoffs",
    ),
    # 6 — June 2
    (
        "In December 1997, Latrell Sprewell was suspended for the entire 1997–98 season — "
        "effectively exiled from the NBA — after choking Golden State Warriors coach P.J. "
        "Carlesimo during practice. The Knicks acquired him in a January 1999 trade. Six "
        "months later he was starting in the NBA Finals, scoring 20 points in Game 4 against "
        "San Antonio, and became one of the most beloved players in MSG history. His "
        "redemption arc — from league pariah to playoff hero in under two years — remains "
        "one of the most improbable in the sport.",
        "Latrell Sprewell, 1999",
    ),
    # 7 — June 3
    (
        "On July 1, 2010 — the first moment NBA free agency opened — the Knicks signed "
        "Amar'e Stoudemire to a five-year, $100 million contract, the largest commitment "
        "the franchise had made in years. In his debut season, Stoudemire averaged 25.3 "
        "points and 8.2 rebounds per game, earned an All-Star selection, and gave Knicks fans "
        "their most compelling offensive centerpiece since Patrick Ewing. His arrival set the "
        "stage for the Carmelo Anthony trade seven months later, signaling New York was "
        "serious about rebuilding.",
        "Summer 2010, Knicks Free Agency",
    ),
    # 8 — June 4
    (
        "On February 22, 2011, the Knicks acquired Carmelo Anthony and Chauncey Billups "
        "from Denver, sending Wilson Chandler, Raymond Felton, Danilo Gallinari, Timofey "
        "Mozgov, and draft compensation in return. Carmelo scored 27 points in his debut "
        "four days later. The cost was real — Gallinari became a quality starter for a "
        "decade — but the Knicks got exactly what they wanted: a top-5 scorer in his "
        "prime at Madison Square Garden. Over six-plus seasons, Carmelo posted 10,186 "
        "points in blue-and-orange — second only to Ewing.",
        "February 2011, The Carmelo Trade",
    ),
    # 9 — June 5
    (
        "On January 24, 2014, Carmelo Anthony scored 62 points against the Charlotte "
        "Bobcats at Madison Square Garden — a franchise record that still stands. He reached "
        "the mark in three quarters going 23-for-35, then sat out the fourth with the Knicks "
        "leading by 30. The previous Knicks single-game record was 60, set by Bernard King "
        "on Christmas Day 1984 — the season before Patrick Ewing arrived. Carmelo erased it "
        "by two points, in three quarters, against a team that would finish 7-59.",
        "January 24, 2014 — Carmelo's 62",
    ),
    # 10 — June 6
    (
        "In early February 2012, Jeremy Lin was an undrafted 23-year-old who had been "
        "waived by Golden State and Houston and was sleeping on his brother's couch in "
        "Manhattan. With Carmelo Anthony and Amar'e Stoudemire both sidelined by injuries, "
        "the Knicks had little choice but to start him. On February 4, Lin scored 25 "
        "points with 7 assists against the New Jersey Nets. Linsanity — one of the most "
        "electric individual runs in NBA history — had begun.",
        "February 4, 2012 — Linsanity Begins",
    ),
    # 11 — June 7
    (
        "Over his first seven starts in February 2012, Jeremy Lin averaged 24.4 points "
        "and 9.1 assists per game — numbers that ranked among the best point guard "
        "stretches in the league that month. On February 10, he scored 38 against Kobe "
        "Bryant's Los Angeles Lakers. MSG sold out every game during the streak. In two "
        "weeks, Lin appeared on two Sports Illustrated covers and was the most-searched "
        "person on Google globally. The Knicks went 9-3 in his starts before he tore "
        "his meniscus in March, ending the dream.",
        "February–March 2012, Linsanity",
    ),
    # 12 — June 8
    (
        "Madison Square Garden — 'The World's Most Famous Arena' — has hosted Knicks "
        "basketball since 1968 and operates at a capacity of 19,812 for NBA games. In "
        "the years before the COVID-19 pandemic disrupted the 2019–20 season, the Knicks "
        "maintained one of the longest active home sellout streaks in the NBA, selling "
        "out games even through their darkest rebuilding winters. Premium floor seats at "
        "MSG have commanded the highest prices in the league for most of the past decade "
        "— a testament to a fan base that refuses to look away.",
        "Madison Square Garden",
    ),
    # 13 — June 9
    (
        "In the first round of the 2013 playoffs, Carmelo Anthony averaged 28.3 points "
        "as the Knicks eliminated the Boston Celtics in six games. It turned out to be "
        "the final playoff series of Boston's Kevin Garnett–Paul Pierce–Ray Allen era. "
        "Within weeks, the Celtics traded Pierce and Garnett to Brooklyn for a package "
        "of picks — a deal that aged catastrophically for the Nets (no title, no picks) "
        "while Boston used those assets to draft Jaylen Brown and build the 2024 NBA "
        "champion Celtics. The Knicks didn't just beat Boston — they accidentally "
        "triggered their rival's dynasty.",
        "2013 First Round — Knicks def. Celtics 4-2",
    ),
    # 14 — June 10
    (
        "After eight consecutive missed playoffs — the longest drought in franchise history "
        "since the 1970s — the Knicks returned to the postseason in 2021 under first-year "
        "head coach Tom Thibodeau, finishing 41-31. Julius Randle, previously written off "
        "by New Orleans and the Lakers, won the NBA's Most Improved Player award after "
        "averaging 24.1 points, 10.2 rebounds, and 6.0 assists — a stunning leap that "
        "made him an All-Star. RJ Barrett averaged 17.6 points at age 20. MSG buzzed "
        "with playoff energy for the first time in eight years.",
        "2020–21 Knicks Season",
    ),
    # 15 — June 11
    (
        "In July 2022, Jalen Brunson agreed to a four-year, $104 million deal with the "
        "Knicks — widely viewed as well below market value at a time when comparable "
        "guards were signing for $150+ million. The connection was partly personal: "
        "Brunson's father Rick had been part of the Knicks organization for years. "
        "In his first season, Brunson averaged 24.0 points and 6.2 assists, immediately "
        "making New York one of the East's most cohesive offensive teams. He proved to be "
        "the best value contract in the NBA that offseason.",
        "July 2022 — Jalen Brunson Signs",
    ),
    # 16 — June 12
    (
        "The 2023–24 Knicks went 50-32 — their first 50-win season since 1996–97 and the "
        "second-best record in the Eastern Conference. Jalen Brunson averaged 28.7 points "
        "and 6.7 assists, earning All-NBA Second Team honors — the most by a Knick since "
        "Carmelo Anthony's prime. In the first round, Brunson scored 41 in the series-"
        "clinching win over Philadelphia. The Garden sold out every home game for the "
        "second straight season, and the expectation level in New York shifted from "
        "'make the playoffs' to 'make a run.'",
        "2023–24 Knicks Season",
    ),
    # 17 — June 13
    (
        "In January 2024, the Knicks traded RJ Barrett and Immanuel Quickley to Toronto "
        "for OG Anunoby, one of the NBA's premier two-way wings. Eight months later, they "
        "acquired Karl-Anthony Towns from Minnesota — a seven-time All-Star — for Julius "
        "Randle and Donte DiVincenzo, then added Mikal Bridges from Brooklyn. In the span "
        "of 12 months, the Knicks assembled arguably the most talented roster the franchise "
        "had built since the Ewing years, with Brunson, Bridges, Anunoby, and Towns "
        "forming the core.",
        "2024 Roster Construction",
    ),
    # 18 — June 14
    (
        "The Knicks' most consequential draft moment: May 12, 1985 — winning the first-"
        "ever NBA lottery to select Patrick Ewing. Their most painful: June 26, 2003, "
        "holding the 8th pick and selecting power forward Mike Sweetney. At No. 1 that "
        "night: LeBron James. No. 3: Carmelo Anthony. No. 4: Chris Bosh. No. 5: Dwyane "
        "Wade. The Knicks eventually got Carmelo — in February 2011 — but it cost them "
        "Gallinari, Felton, Mozgov, and multiple first-round picks. Sometimes the draft "
        "lottery is cheaper.",
        "Knicks Draft History",
    ),
    # 19 — June 15
    (
        "For most of the past 25 years, being a Knicks fan meant watching other teams "
        "win while MSG hosted mediocre basketball at premium prices. What changed: patient "
        "reconstruction starting in 2019, Tom Thibodeau's culture overhaul, the under-"
        "market signing of Jalen Brunson, and a run of aggressive trades in 2024 that "
        "brought in OG Anunoby, Karl-Anthony Towns, and Mikal Bridges. For the first "
        "time since the Ewing era, a Knicks championship run felt genuinely plausible — "
        "and Boston's 2024 title, built on picks extracted from Brooklyn's failed dynasty "
        "attempt, began the day Carmelo's Knicks eliminated the Celtics in 2013.",
        "The Knicks' Window, 2024–Present",
    ),
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
    _knicks_start = date(2026, 5, 27)
    _knicks_end   = date(2026, 6, 15)
    if _knicks_start <= _today <= _knicks_end:
        _fact_text, _fact_attr = KNICKS_FACTS[(_today - _knicks_start).days]
        quote_inner = (
            f'<p style="font-style:italic;color:#e2e8f0;font-size:13px;line-height:1.65;'
            f'margin:0;font-weight:400;font-family:{_FONT}">{_fact_text}</p>'
            f'<div style="color:#f07030;font-size:11px;margin-top:7px;font-weight:400;'
            f'font-family:{_FONT}">&#8212; {_fact_attr}</div>'
        )
    else:
        stoic_text, stoic_author = random.choice(STOIC_QUOTES)
        quote_inner = (
            f'<p style="font-style:italic;color:#e2e8f0;font-size:13px;line-height:1.65;'
            f'margin:0;font-weight:400;font-family:{_FONT}">&#8220;{stoic_text}&#8221;</p>'
            f'<div style="color:#f07030;font-size:11px;margin-top:7px;font-weight:400;'
            f'font-family:{_FONT}">&#8212; {stoic_author}</div>'
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

  <!-- Daily quote / Knicks fact -->
  <div style="background:#1a1a2e;padding:16px 32px 14px">
    {quote_inner}
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

  <!-- Finance Corner -->
  {_finance_corner_section(briefing.get("finance_corner", []))}

  <!-- Other sections: Partner, Advertiser, Social, UK Market -->
  {other_sections}

  <!-- Policy notes -->
  {policy_block}

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
