"""Row shapes for the tables in schema.sql. Keep the two in sync."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Source:
    id: int
    type: str  # 'rss', 'blog', 'youtube'
    name: str
    url: str
    active: bool
    created_at: datetime


@dataclass
class Item:
    id: int
    source_id: int
    external_id: str
    title: str | None
    raw_content: str | None
    markdown_content: str | None
    summary: str | None
    published_at: datetime | None
    fetched_at: datetime
    sent: bool


@dataclass
class Digest:
    id: int
    sent_at: datetime
    item_count: int | None
    content: str | None


@dataclass
class Subscriber:
    id: int
    email: str
    active: bool
    subscribed_at: datetime
