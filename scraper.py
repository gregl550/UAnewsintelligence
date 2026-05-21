import calendar
import concurrent.futures
import html
import logging
import re
from datetime import datetime, timedelta, timezone

import feedparser

from config import MAX_CONTENT_CHARS, RSS_FEEDS

logger = logging.getLogger(__name__)


def _clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:MAX_CONTENT_CHARS]


def _parse_feed(name: str, url: str, cutoff: datetime) -> list[dict]:
    try:
        feed = feedparser.parse(
            url,
            request_headers={"User-Agent": "Mozilla/5.0 UniversalAdsIntelBot/1.0"},
        )
        if feed.bozo and not feed.entries:
            logger.warning(f"  {name}: feed error — {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries:
            pub_date = None
            for field in ("published_parsed", "updated_parsed", "created_parsed"):
                raw = getattr(entry, field, None)
                if raw:
                    pub_date = datetime(
                        *raw[:6], tzinfo=timezone.utc
                    )
                    break

            if pub_date is None:
                continue
            if pub_date < cutoff:
                continue

            content = ""
            if getattr(entry, "content", None):
                content = _clean_html(entry.content[0].value)
            elif getattr(entry, "summary", None):
                content = _clean_html(entry.summary)
            elif getattr(entry, "description", None):
                content = _clean_html(entry.description)

            articles.append(
                {
                    "source": name,
                    "title": (entry.get("title") or "").strip(),
                    "url": entry.get("link") or entry.get("id") or "",
                    "published": pub_date.strftime("%Y-%m-%d %H:%M UTC"),
                    "content": content,
                }
            )

        logger.info(f"  {name}: {len(articles)} article(s) in past 24 h")
        return articles

    except Exception as exc:
        logger.error(f"  {name}: fetch failed — {exc}")
        return []


def scrape_news(hours: int = 24) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    all_articles: list[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futures = {
            pool.submit(_parse_feed, name, url, cutoff): name
            for name, url in RSS_FEEDS.items()
        }
        for future in concurrent.futures.as_completed(futures):
            all_articles.extend(future.result())

    all_articles.sort(key=lambda a: a["published"], reverse=True)
    return all_articles
