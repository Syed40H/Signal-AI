"""Finds new videos on a YouTube channel and grabs their transcripts."""

from dataclasses import replace

from youtube_transcript_api import YouTubeTranscriptApi

from app.db.models import RawItem
from app.ingestion.rss import fetch_rss

# Every channel has a public feed of its latest 15 uploads, so no API key is needed.
FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"

_transcripts = YouTubeTranscriptApi()


def fetch_youtube_channel(channel_id: str) -> list[RawItem]:
    videos = []
    for item in fetch_rss(FEED_URL.format(channel_id)):
        if item.url and "/shorts/" in item.url:
            continue  # Shorts are too short to be worth summarizing
        # Feed ids look like "yt:video:<id>", keep just the video id
        videos.append(replace(item, external_id=item.external_id.removeprefix("yt:video:")))
    return videos


def load_transcript(item: RawItem) -> str:
    transcript = _transcripts.fetch(item.external_id, languages=["en"])
    return " ".join(snippet.text for snippet in transcript.snippets)
