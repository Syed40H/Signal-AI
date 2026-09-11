"""Checks every active source and stores anything new."""

import logging
from datetime import datetime, timedelta, timezone

import psycopg

from app.db.models import Source
from app.db.queries import insert_items
from app.ingestion.rss import fetch_rss

log = logging.getLogger(__name__)

FETCHERS = {
    "rss": fetch_rss,
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
            new = insert_items(conn, source.id, items)
            conn.commit()
        except Exception:
            conn.rollback()
            log.exception("Couldn't ingest %s, moving on", source.name)
            continue

        log.info("%s: %d new (%d recent in feed)", source.name, new, len(items))
        total_new += new

    return total_new
