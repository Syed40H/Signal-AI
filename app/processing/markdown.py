"""Turns an item's raw content into markdown before it gets summarized."""

import re

from bs4 import BeautifulSoup
from markdownify import markdownify


def to_markdown(raw: str) -> str:
    # Transcripts and scraped blog posts are already plain text, only feed bodies are HTML
    if BeautifulSoup(raw, "html.parser").find() is None:
        return raw.strip()
    md = markdownify(raw, heading_style="ATX", strip=["img"])
    return re.sub(r"\n{3,}", "\n\n", md).strip()
