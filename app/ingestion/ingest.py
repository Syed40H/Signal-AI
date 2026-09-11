"""Checks every active source and stores anything new."""

import logging
from datetime import datetime, timedelta, timezone

import psycopg

from app.db.models import RawItem, Source
from app.db.queries import insert_items, update_item_content
from app.ingestion.blogs import fetch_anthropic_news, load_article
from app.ingestion.rss import fetch_rss
from app.ingestion.youtube import fetch_youtube_channel, load_transcript

log = logging.getLogger(__name__)

# How to list the latest items for each kind of source.
FETCHERS = {
    "rss": fetch_rss,
    "blog": fetch_anthropic_news,
    "youtube": fetch_youtube_channel,
}

# Full content is slow (and for YouTube rate limited) to download, so it's only fetched for new items.
CONTENT_LOADERS = {
    "blog": load_article,
    "youtube": load_transcript,
}

# Only keep recent posts, so a new source doesn't dump its whole back catalogue into the digest.
MAX_AGE = timedelta(days=3)


def ingest_all(conn: psycopg.Connection, sources: list[Source]) -> int:
    """Fetch every source and store new items. Returns the total number of new items."""
    cutoff = datetime.now(timezone.utc) - MAX_AGE
    total_new = 0

    for source in sources:
        fetch = FETCHERS.get(source.type)
        if fetch is None:
            log.warning("No fetcher for %s sources yet, skipping %s", source.type, source.name)
            continue

        # One broken source shouldn't stop the rest of the run.
        try:
            items = [i for i in fetch(source.url) if i.published_at is None or i.published_at >= cutoff]
            new_items = insert_items(conn, source.id, items)
            _load_content(conn, source, new_items)
            conn.commit()
        except Exception:
            conn.rollback()
            log.exception("Couldn't ingest %s, moving on", source.name)
            continue

        log.info("%s: %d new (%d recent)", source.name, len(new_items), len(items))
        total_new += len(new_items)

    return total_new


def _load_content(conn: psycopg.Connection, source: Source, new_items: list[tuple[int, RawItem]]) -> None:
    load = CONTENT_LOADERS.get(source.type)
    if load is None:
        return
    for item_id, item in new_items:
        # If this fails the item is still kept, just with the short description it came with.
        try:
            content = load(item)
        except Exception as exc:
            log.warning("No full content for %s (%s)", item.url, type(exc).__name__)
            continue
        update_item_content(conn, item_id, content)
