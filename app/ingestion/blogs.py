"""Scrapes Anthropic's news page, since it doesn't have an RSS feed."""

import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from app.db.models import RawItem
from app.ingestion.rss import USER_AGENT


def fetch_anthropic_news(url: str) -> list[RawItem]:
    soup = _get_page(url)
    posts: dict[str, RawItem] = {}

    # Every post on the page (featured cards and the list below them) is a link with a <time> inside.
    for link in soup.find_all("a", href=True):
        time = link.find("time")
        if time is None:
            continue
        post_url = urljoin(url, link["href"])
        if post_url in posts:
            continue  # featured posts show up in the list too

        heading = link.find(re.compile(r"^h[1-6]$"))
        if heading:
            title = heading.get_text(" ", strip=True)
        else:
            # List rows are a div with the date and category, then the title
            meta = time.parent
            title = " ".join(c.get_text(" ", strip=True) for c in link.children if isinstance(c, Tag) and c is not meta)

        excerpt = link.find("p")
        posts[post_url] = RawItem(
            external_id=post_url,
            title=title or None,
            url=post_url,
            raw_content=excerpt.get_text(" ", strip=True) if excerpt else None,
            published_at=_parse_date(time.get_text(strip=True)),
        )

    return list(posts.values())


MAX_ARTICLE_CHARS = 100_000


def load_article(item: RawItem) -> str:
    """Returns the readable text of a post (headings, paragraphs and lists)."""
    soup = _get_page(item.url)
    # The outermost <article> is the whole post. Nested ones are quotes, sections or footer boxes.
    body = next((a for a in soup.find_all("article") if a.find_parent("article") is None), None) or soup.find("main")
    if body is None:
        raise ValueError("couldn't find the post body")

    blocks = [b.get_text(" ", strip=True) for b in body.find_all(["h2", "h3", "h4", "p", "li"])]
    text = "\n\n".join(b for b in blocks if b) or body.get_text(" ", strip=True)
    # Some posts are full reports, far more than a summary needs
    return text[:MAX_ARTICLE_CHARS]


def _get_page(url: str) -> BeautifulSoup:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _parse_date(text: str) -> datetime | None:
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None
