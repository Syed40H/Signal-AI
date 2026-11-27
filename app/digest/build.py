"""Puts the summaries that haven't been sent yet together into one email."""

from dataclasses import dataclass
from datetime import datetime
from html import escape
from itertools import groupby


@dataclass
class DigestEmail:
    subject: str
    html: str
    text: str
    item_ids: list[int]


def build_digest(items: list[dict], today: datetime) -> DigestEmail | None:
    """Items come from queries.unsent_summaries, already ordered by source. Returns None if there's nothing new."""
    if not items:
        return None

    date = f"{today:%A} {today.day} {today:%B}"
    intro = f"{len(items)} new things in AI, {date}"
    html = [
        '<div style="max-width:640px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;color:#222;line-height:1.5">',
        '<h1 style="margin:0 0 4px;font-size:26px">Signal AI</h1>',
        f'<p style="margin:0 0 24px;color:#666">{intro}</p>',
    ]
    text = [f"Signal AI - {intro}", ""]

    for source, group in groupby(items, key=lambda i: i["source_name"]):
        html.append(
            f'<h2 style="margin:28px 0 8px;padding-bottom:4px;border-bottom:1px solid #ddd;font-size:18px">{escape(source)}</h2>'
        )
        text += [source.upper(), ""]

        for item in group:
            title = item["title"] or "Untitled"
            if item["url"]:
                heading = f'<a href="{escape(item["url"], quote=True)}" style="color:#1a56db;text-decoration:none">{escape(title)}</a>'
            else:
                heading = escape(title)
            html.append(f'<h3 style="margin:16px 0 4px;font-size:16px">{heading}</h3>')
            html.append(f'<p style="margin:0">{escape(item["summary"])}</p>')

            text += [f"* {title}", item["summary"]]
            if item["url"]:
                text.append(item["url"])
            text.append("")

    html.append("</div>")
    return DigestEmail(
        subject=f"Signal AI: {len(items)} new in AI ({today.day} {today:%b})",
        html="\n".join(html),
        text="\n".join(text),
        item_ids=[item["id"] for item in items],
    )
