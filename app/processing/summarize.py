"""Summarizes new items with Gemini."""

import logging
import time

import psycopg
from google import genai
from google.genai import errors, types

from app.db.queries import pending_summaries, save_summary
from app.processing.markdown import to_markdown

log = logging.getLogger(__name__)

MODEL = "gemini-3.5-flash-lite"
# Plain text in, plain text out. Turning off function calling also stops the SDK warning on every call.
CONFIG = types.GenerateContentConfig(
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

# The free tier has per-minute and per-day limits, so go easy and cap each run.
MAX_PER_RUN = 30
PAUSE_SECONDS = 4

PROMPT = """You're writing one entry for a daily AI news digest email.
Summarize this {kind} in 2-4 sentences: what's new and why it matters.
Write plain text, no intro like "This article" and no bullet points.

Title: {title}
Source: {source}

{content}"""

KINDS = {"rss": "article", "blog": "blog post", "youtube": "video transcript"}


def summarize_pending(conn: psycopg.Connection, api_key: str) -> int:
    """Summarize items that don't have a summary yet. Returns how many got one."""
    client = genai.Client(api_key=api_key)
    items = pending_summaries(conn, MAX_PER_RUN)
    done = 0

    for item in items:
        markdown = to_markdown(item["raw_content"])
        prompt = PROMPT.format(
            kind=KINDS.get(item["source_type"], "post"),
            title=item["title"],
            source=item["source_name"],
            content=markdown,
        )
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt, config=CONFIG)
        except errors.ClientError as exc:
            if exc.code == 429:
                log.warning("Hit the Gemini free tier limit, the rest will be summarized next run")
                break
            log.warning("Couldn't summarize %r (%s)", item["title"], exc.message)
            continue
        except errors.ServerError as exc:
            log.warning("Gemini had a problem with %r (%s)", item["title"], exc.message)
            continue

        summary = (response.text or "").strip()
        if not summary:
            log.warning("Got an empty summary for %r", item["title"])
            continue

        save_summary(conn, item["id"], markdown, summary)
        conn.commit()
        done += 1
        time.sleep(PAUSE_SECONDS)

    left = len(items) - done
    log.info("Summarized %d items%s", done, f" ({left} left for next run)" if left else "")
    return done
