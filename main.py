#!/usr/bin/env python3
"""Universal Ads News Intelligence Agent — daily briefing runner."""

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
        logging.FileHandler(_LOG_DIR / "agent.log"),
    ],
)
logger = logging.getLogger(__name__)


def _check_env() -> None:
    required = ["ANTHROPIC_API_KEY", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        logger.error(f"Missing required env vars: {', '.join(missing)}")
        logger.error("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


def _load_previous_briefing() -> tuple[set[str], list[str]]:
    archive_dir = Path(__file__).parent / "logs" / "archive"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    fname = archive_dir / f"briefing_{yesterday}.json"
    if not fname.exists():
        logger.info("  No previous briefing found — proceeding without deduplication")
        return set(), []
    try:
        with open(fname) as f:
            data = json.load(f)
        briefing = data.get("briefing", {})
        seen_urls: set[str] = set()
        for story in briefing.get("top_stories", []):
            if story.get("url"):
                seen_urls.add(story["url"])
        ci = briefing.get("competitive_intel", {})
        for competitor_items in ci.values():
            if isinstance(competitor_items, list):
                for item in competitor_items:
                    if item.get("url"):
                        seen_urls.add(item["url"])
        for section in ["partner_signals", "advertiser_trends", "social_media", "uk_market", "policy_regulation", "finance_corner", "ua_partners"]:
            for item in briefing.get(section, []):
                if item.get("url"):
                    seen_urls.add(item["url"])
        prev_headlines = [s["title"] for s in briefing.get("top_stories", []) if s.get("title")]
        logger.info(f"  Loaded previous briefing: {len(seen_urls)} seen URLs, {len(prev_headlines)} top headlines")
        return seen_urls, prev_headlines
    except Exception as exc:
        logger.warning(f"  Could not load previous briefing: {exc}")
        return set(), []


def _save_backup(briefing: dict, article_count: int) -> None:
    archive_dir = Path(__file__).parent / "logs" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    fname = archive_dir / f"briefing_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(fname, "w") as f:
        json.dump({"article_count": article_count, "briefing": briefing}, f, indent=2)
    logger.info(f"  Briefing saved to {fname}")


def main() -> None:
    logger.info("━" * 60)
    logger.info("Universal Ads News Intelligence Agent — starting")
    logger.info("━" * 60)

    _check_env()

    # Step 1: Scrape (72h on Mondays to cover the full weekend)
    is_monday = datetime.now().weekday() == 0
    hours = 72 if is_monday else 24
    logger.info(f"STEP 1 — Scraping RSS feeds (past {hours} h)")
    from scraper import scrape_news
    articles = scrape_news(hours=hours)
    logger.info(f"  Total articles in past {hours} h: {len(articles)}")

    if not articles:
        logger.warning("No articles found. Exiting without sending email.")
        return

    # Step 2: Analyze
    logger.info("STEP 2 — Analyzing with Claude")
    from analyzer import analyze_articles
    import anthropic as _anthropic
    seen_urls, prev_headlines = _load_previous_briefing()
    try:
        briefing = analyze_articles(articles, seen_urls=seen_urls, prev_headlines=prev_headlines)
    except _anthropic.APITimeoutError:
        logger.error("Claude API timed out on all 3 attempts (120s each). Exiting without sending email.")
        sys.exit(1)
    except Exception as exc:
        logger.error(f"Claude analysis failed after all retries: {exc}. Exiting without sending email.")
        sys.exit(1)

    # Step 3: Save backup
    logger.info("STEP 3 — Saving archive copy")
    _save_backup(briefing, len(articles))

    # Step 4: Send email
    logger.info("STEP 4 — Sending briefing email")
    from emailer import send_briefing
    send_briefing(briefing, article_count=len(articles))

    logger.info("━" * 60)
    logger.info("Done. Have a great day!")
    logger.info("━" * 60)


if __name__ == "__main__":
    main()
