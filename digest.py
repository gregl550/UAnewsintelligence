#!/usr/bin/env python3
"""
Weekly Friday Digest — rolls up the past 5 weekday briefings into a
"5 Biggest Stories of the Week" email, easy to forward to leadership.

Called by the GitHub Actions `friday_digest.yml` workflow every Friday.
Can also be run manually:  python digest.py
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

_LOG_DIR = Path(__file__).parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_LOG_DIR / "digest.log"),
    ],
)
logger = logging.getLogger(__name__)

ARCHIVE_DIR = Path(__file__).parent / "logs" / "archive"


def _load_week_briefings() -> list[dict]:
    """Load the last 5 weekday archive JSON files (Mon-Fri)."""
    today = datetime.now().date()
    found = []
    for days_back in range(1, 8):
        d = today - timedelta(days=days_back)
        if d.weekday() >= 5:
            continue
        fname = ARCHIVE_DIR / f"briefing_{d.strftime('%Y-%m-%d')}.json"
        if fname.exists():
            try:
                data = json.loads(fname.read_text())
                data["_date"] = d.strftime("%Y-%m-%d")
                found.append(data)
                logger.info(f"  Loaded {fname.name}")
            except Exception as exc:
                logger.warning(f"  Could not load {fname.name}: {exc}")
        if len(found) >= 5:
            break
    return list(reversed(found))


def _pick_top_stories(week_data: list[dict], n: int = 5) -> list[dict]:
    seen_urls: set[str] = set()
    all_stories: list[dict] = []
    for day in week_data:
        date_str = day.get("_date", "")
        briefing = day.get("briefing", {})
        for story in briefing.get("top_stories", []):
            url = story.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            story = dict(story)
            story["_day_date"] = date_str
            all_stories.append(story)
    all_stories.sort(key=lambda s: s.get("relevance_score", 0), reverse=True)
    return all_stories[:n]


def _week_label(week_data: list[dict]) -> str:
    if not week_data:
        return datetime.now().strftime("Week of %b %-d")
    start = week_data[0].get("_date", "")
    end   = week_data[-1].get("_date", "")
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt   = datetime.strptime(end,   "%Y-%m-%d")
        return f"Week of {start_dt.strftime('%b %-d')} - {end_dt.strftime('%b %-d, %Y')}"
    except Exception:
        return datetime.now().strftime("Week of %b %-d")


def _build_digest_html(stories: list[dict], week_label: str) -> str:
    from emailer import _FONT

    story_rows = []
    for i, s in enumerate(stories):
        rank    = i + 1
        title   = s.get("title", "Untitled")
        url     = s.get("url", "#")
        source  = s.get("source", "")
        pub     = s.get("published", s.get("_day_date", ""))
        summary = s.get("summary", "")
        impl    = s.get("ua_implications") or s.get("ua_implication", "")
        score   = s.get("relevance_score", 3)
        rank_color = {5: "#c00", 4: "#e65100"}.get(score, "#003087")

        impl_block = ""
        if impl:
            impl_block = (
                f'<div style="background:#fef9e7;border:1px solid #f6d860;border-radius:4px;'
                f'padding:6px 10px;margin-top:6px;font-size:12px;color:#5a4400;line-height:1.4;'
                f'font-family:{_FONT}">'
                f'<b style="color:#b8860b">UA Signal:</b> {impl}</div>'
            )

        border = "none" if i == len(stories) - 1 else "1px solid #f7fafc"
        story_rows.append(
            f'<div style="padding:14px 32px;border-bottom:{border}">'
            f'<div style="display:flex;align-items:flex-start;gap:10px">'
            f'<span style="display:inline-block;min-width:24px;height:24px;border-radius:50%;'
            f'background:{rank_color};color:#fff;font-size:12px;font-weight:800;'
            f'text-align:center;line-height:24px;flex-shrink:0">{rank}</span>'
            f'<div style="flex:1">'
            f'<div style="font-size:14px;font-weight:600;line-height:1.3;color:#1a202c;font-family:{_FONT}">'
            f'<a href="{url}" style="color:#1a202c;text-decoration:none">{title}</a></div>'
            f'<div style="color:#8895a7;font-size:11px;margin-top:2px;font-family:{_FONT}">'
            f'{source}{" &bull; " if source and pub else ""}{pub}</div>'
            f'<div style="font-size:13px;line-height:1.45;margin-top:5px;color:#3d4852;font-family:{_FONT}">{summary}</div>'
            f'{impl_block}'
            f'</div></div></div>'
        )

    stories_block = "".join(story_rows)
    run_date = datetime.now().strftime("%B %-d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UA Weekly Digest - {week_label}</title>
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:{_FONT};color:#1a202c">
<div style="max-width:680px;margin:0 auto">

  <!-- Header -->
  <div style="background:#060608;background:radial-gradient(ellipse at 20% 70%,rgba(120,40,140,.5) 0%,transparent 55%),radial-gradient(ellipse at 85% 15%,rgba(30,90,120,.45) 0%,transparent 55%),#060608;padding:22px 32px 16px">
    <h1 style="color:#fff;margin:0;font-size:28px;font-weight:700;letter-spacing:-.8px;font-family:{_FONT}">Universal Ads</h1>
    <div style="height:4px;background:linear-gradient(90deg,#e8402a 0%,#f07030 50%,#4a7fd4 100%);border-radius:3px;margin:10px 0 9px"></div>
    <div style="color:#9ca3af;font-size:11px;font-weight:400;letter-spacing:.8px;text-transform:uppercase;margin:0 0 5px;font-family:{_FONT}">Weekly Intelligence Digest</div>
    <div style="color:#6b7280;font-size:12px;margin-top:4px;font-family:{_FONT}">{week_label}</div>
  </div>

  <!-- Intro -->
  <div style="background:#fff;border-left:4px solid #003087;padding:14px 32px">
    <p style="font-size:14px;font-weight:600;color:#003087;margin:0 0 6px;font-family:{_FONT}">5 Biggest Stories of the Week</p>
    <p style="font-size:13px;line-height:1.5;color:#3d4852;margin:0;font-family:{_FONT}">
      The highest-impact stories from this week's daily briefings, ranked by relevance to Universal Ads.
      Easy to forward - click any headline for the full article.
    </p>
  </div>

  <!-- Stories -->
  <div style="background:#fff;margin-top:8px">
    <div style="padding:9px 32px;border-bottom:1px solid #edf2f7">
      <h2 style="margin:0;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#003087;font-weight:700;font-family:{_FONT}">Top Stories This Week</h2>
    </div>
    {stories_block}
  </div>

  <!-- Footer -->
  <div style="background:#edf2f7;padding:10px 32px;font-size:11px;color:#8895a7;text-align:center;margin-top:8px;font-family:{_FONT}">
    UA Weekly Digest &bull; Powered by Claude AI &bull; {run_date}<br>
    <span style="font-size:10px">Compiled from your daily UA Intelligence Briefings</span>
  </div>

</div>
</body>
</html>"""


def main() -> None:
    logger.info("=" * 60)
    logger.info("UA Weekly Digest - starting")
    logger.info("=" * 60)

    required = ["ANTHROPIC_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        logger.error(f"Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    logger.info("STEP 1 - Loading week's archive briefings")
    week_data = _load_week_briefings()
    if not week_data:
        logger.warning("No archive briefings found for this week. Exiting.")
        return
    logger.info(f"  Loaded {len(week_data)} briefing(s)")

    logger.info("STEP 2 - Selecting top 5 stories of the week")
    top_stories = _pick_top_stories(week_data, n=5)
    logger.info(f"  Selected {len(top_stories)} stories")

    week_label = _week_label(week_data)

    logger.info("STEP 3 - Building digest HTML")
    html = _build_digest_html(top_stories, week_label)

    logger.info("STEP 4 - Sending weekly digest")
    sender_name = os.environ.get("SENDER_NAME", "Universal Ads Intelligence")
    recipient   = os.environ.get("RECIPIENT_EMAIL", os.environ.get("GMAIL_ADDRESS", ""))
    subject     = f"UA Weekly Digest - {week_label}"

    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{sender_name} <{os.environ['GMAIL_ADDRESS']}>"
    msg["To"]      = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        smtp.sendmail(os.environ["GMAIL_ADDRESS"], recipient, msg.as_string())
    logger.info(f"  Digest sent to {recipient}")

    logger.info("=" * 60)
    logger.info("Weekly digest done.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
