"""Signal AI entrypoint: runs one pass of the pipeline."""

import logging
import sys

from app.config import SOURCES, load_settings
from app.db.connection import connect, init_schema
from app.db.queries import sync_sources
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

        for table in TABLES:
            count = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]
            log.info("  %-12s %d rows", table, count)

    # Later steps plug in here: build digest -> deliver.


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        run_pipeline()
    except Exception:
        log.exception("Pipeline run failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
