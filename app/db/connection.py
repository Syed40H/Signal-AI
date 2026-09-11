"""Postgres connection helpers."""

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(database_url: str) -> psycopg.Connection:
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10)


def init_schema(conn: psycopg.Connection) -> None:
    """Apply schema.sql. Every statement is idempotent, so this is safe on every run."""
    conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
