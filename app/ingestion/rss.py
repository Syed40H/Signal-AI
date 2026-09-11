"""Fetches an RSS/Atom feed and turns its entries into RawItems."""

from datetime import datetime, timezone

import feedparser
import requests

from app.db.models import RawItem

USER_AGENT = "SignalAI/0.1 (personal news digest)"


def fetch_rss(url: str) -> list[RawItem]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    response.raise_for_status()

    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise ValueError(f"couldn't parse feed: {feed.bozo_exception}")

    items = []
    for entry in feed.entries:
        external_id = entry.get("id") or entry.get("link")
        if not external_id:
            continue  # nothing stable to dedup on

        if entry.get("content"):
            body = entry.content[0].value
        else:
            body = entry.get("summary")

        # feedparser gives these as UTC time tuples
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        published_at = datetime(*parsed[:6], tzinfo=timezone.utc) if parsed else None

        items.append(
            RawItem(
                external_id=external_id,
                title=entry.get("title"),
                url=entry.get("link"),
                raw_content=body,
                published_at=published_at,
            )
        )
    return items
