"""Signal AI entrypoint: runs one pass of the pipeline."""

import logging
import sys
from datetime import datetime

import psycopg

from app.config import SOURCES, Settings, load_settings
from app.db.connection import connect, init_schema
from app.db.queries import record_digest, sync_sources, unsent_summaries
from app.delivery.email import send_digest
from app.digest.build import build_digest
from app.ingestion.ingest import ingest_all
from app.processing.summarize import summarize_pending

log = logging.getLogger("signal_ai")

TABLES = ("sources", "items", "digests", "subscribers")


def run_pipeline() -> None:
    settings = load_settings()

    with connect(settings.database_url) as conn:
        init_schema(conn)
        version = conn.execute("SHOW server_version").fetchone()["server_version"]
        log.info("Connected to Postgres %s, schema is up to date", version)

        sources = sync_sources(conn, SOURCES)
        new = ingest_all(conn, sources)
        log.info("Ingested %d new items from %d sources", new, len(sources))

        if settings.gemini_api_key:
            summarize_pending(conn, settings.gemini_api_key)
        else:
            log.warning("GEMINI_API_KEY isn't set, skipping summaries")

        send_todays_digest(conn, settings)

        for table in TABLES:
            count = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            log.info("  %-12s %d rows", table, count)


def send_todays_digest(conn: psycopg.Connection, settings: Settings) -> None:
    if not (settings.resend_api_key and settings.digest_recipient):
        log.warning("RESEND_API_KEY or DIGEST_RECIPIENT isn't set, skipping the email")
        return

    digest = build_digest(unsent_summaries(conn), datetime.now())
    if digest is None:
        log.info("Nothing new to send")
        return

    email_id = send_digest(digest, settings.resend_api_key, settings.email_from, settings.digest_recipient)
    # Only mark items as sent once the email has actually gone out
    record_digest(conn, digest.item_ids, digest.text)
    conn.commit()
    log.info("Emailed a digest with %d items (Resend id %s)", len(digest.item_ids), email_id)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # The HTTP and Gemini libraries log every request, which drowns out the pipeline's own logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    try:
        run_pipeline()
    except Exception:
        log.exception("Pipeline run failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
