"""Loads runtime configuration from environment variables (and a local .env file)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class SourceConfig:
    type: str  # 'rss', 'blog', 'youtube'
    name: str
    url: str


# What the pipeline monitors. Removing one here stops it being checked.
SOURCES = [
    # News sites
    SourceConfig("rss", "The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    SourceConfig("rss", "MIT Technology Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    SourceConfig("rss", "Simon Willison", "https://simonwillison.net/atom/everything/"),
    # Company blogs (OpenAI has a feed, Anthropic doesn't so its news page gets scraped)
    SourceConfig("rss", "OpenAI News", "https://openai.com/news/rss.xml"),
    SourceConfig("blog", "Anthropic News", "https://www.anthropic.com/news"),
    # YouTube channels (url is the channel id)
    SourceConfig("youtube", "Dubibubi", "UC4SgqYQmdTCKXUoer2U-lcg"),
    SourceConfig("youtube", "Tina Huang", "UC2UXDak6o7rBm23k3Vv5dww"),
    SourceConfig("youtube", "Sajjaad Khader", "UC7zZ2-Q_oxbUaoMVL0z51wg"),
    SourceConfig("youtube", "Duke Pan", "UCxE6qpCeMGgyrae2fV-Lhhg"),
    SourceConfig("youtube", "Starter Story", "UChhw6DlKKTQ9mYSpTfXUYqA"),
    SourceConfig("youtube", "Pat Simmons", "UCY8ZKVxXj0FgIvSfeiSDclg"),
    SourceConfig("youtube", "David Ondrej", "UCPGrgwfbkjTIgPoOh2q1BAg"),
]


@dataclass(frozen=True)
class Settings:
    database_url: str
    openai_api_key: str | None
    youtube_api_key: str | None
    email_api_key: str | None
    email_from: str | None
    digest_recipient: str | None


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def load_settings() -> Settings:
    # Real environment variables win over .env, so values set on Render take precedence.
    load_dotenv()

    database_url = _optional("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")

    return Settings(
        database_url=database_url,
        openai_api_key=_optional("OPENAI_API_KEY"),
        youtube_api_key=_optional("YOUTUBE_API_KEY"),
        email_api_key=_optional("EMAIL_API_KEY"),
        email_from=_optional("EMAIL_FROM"),
        digest_recipient=_optional("DIGEST_RECIPIENT"),
    )
