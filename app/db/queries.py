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


def insert_items(conn: psycopg.Connection, source_id: int, items: list[RawItem]) -> list[tuple[int, RawItem]]:
    """Store items for a source, skipping any already saved. Returns the new ones with their ids."""
    new = []
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
            new.append((row["id"], item))
    return new


def update_item_content(conn: psycopg.Connection, item_id: int, raw_content: str) -> None:
    conn.execute("UPDATE items SET raw_content = %s WHERE id = %s", (raw_content, item_id))


def pending_summaries(conn: psycopg.Connection, limit: int) -> list[dict]:
    """Unsent items that still need a summary, oldest first."""
    return conn.execute(
        """
        SELECT i.id, i.title, i.raw_content, s.type AS source_type, s.name AS source_name
        FROM items i JOIN sources s ON s.id = i.source_id
        WHERE i.summary IS NULL AND i.raw_content IS NOT NULL AND NOT i.sent
        ORDER BY i.published_at NULLS LAST, i.id
        LIMIT %s
        """,
        (limit,),
    ).fetchall()


def save_summary(conn: psycopg.Connection, item_id: int, markdown: str, summary: str) -> None:
    conn.execute(
        "UPDATE items SET markdown_content = %s, summary = %s WHERE id = %s",
        (markdown, summary, item_id),
    )


def unsent_summaries(conn: psycopg.Connection) -> list[dict]:
    """Summarized items that haven't been in a digest yet, grouped by source."""
    return conn.execute(
        """
        SELECT i.id, i.title, i.url, i.summary, s.name AS source_name
        FROM items i JOIN sources s ON s.id = i.source_id
        WHERE i.summary IS NOT NULL AND NOT i.sent
        ORDER BY s.type, s.name, i.published_at DESC NULLS LAST
        """
    ).fetchall()


def record_digest(conn: psycopg.Connection, item_ids: list[int], content: str) -> None:
    """Save a sent digest and mark its items as sent so they never go out twice."""
    conn.execute("INSERT INTO digests (item_count, content) VALUES (%s, %s)", (len(item_ids), content))
    conn.execute("UPDATE items SET sent = TRUE WHERE id = ANY(%s)", (item_ids,))
