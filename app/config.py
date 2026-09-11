"""Loads runtime configuration from environment variables (and a local .env file)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


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
    # Real environment variables win over .env, so docker-compose/Render overrides apply.
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
