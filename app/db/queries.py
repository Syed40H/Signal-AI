"""Database reads and writes used by the pipeline."""

import psycopg

from app.config import SourceConfig
from app.db.models import RawItem, Source


def sync_sources(conn: psycopg.Connection, configs: list[SourceConfig]) -> list[Source]:
    """Make the sources table match the configured list and return the active sources."""
    for cfg in configs:
        conn.execute(
            """
            INSERT INTO sources (type, name, url) VALUES (%s, %s, %s)
            ON CONFLICT (type, url) DO UPDATE SET name = EXCLUDED.name, active = TRUE
            """,
            (cfg.type, cfg.name, cfg.url),
        )

    # Sources removed from the config stop being checked, but their items are kept.
    keys = [f"{cfg.type}|{cfg.url}" for cfg in configs]
    conn.execute("UPDATE sources SET active = FALSE WHERE type || '|' || url <> ALL(%s)", (keys,))
    conn.commit()

    rows = conn.execute("SELECT * FROM sources WHERE active ORDER BY id").fetchall()
    return [Source(**row) for row in rows]


def insert_items(conn: psycopg.Connection, source_id: int, items: list[RawItem]) -> int:
    """Store items for a source, skipping any already saved. Returns how many were new."""
    new = 0
    for item in items:
        row = conn.execute(
            """
            INSERT INTO items (source_id, external_id, title, url, raw_content, published_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, external_id) DO NOTHING
            RETURNING id
            """,
            (source_id, item.external_id, item.title, item.url, item.raw_content, item.published_at),
        ).fetchone()
        if row is not None:
            new += 1
    return new
