# Signal AI

Keeping up with AI news is a lot, so I built something to do it for me. Signal AI checks a bunch of AI sources (RSS feeds, company blogs and YouTube channels), summarizes anything new with Google's Gemini API, and emails me a daily digest.

It's still a work in progress. Right now it collects new posts and videos from all the sources, and I'm working on the summaries and the email next.

## How it works

1. Check each source for new posts or videos
2. Pull the content (article text or video transcript)
3. Summarize each one with Gemini
4. Put the summaries together into one email
5. Send it and mark those items as sent so nothing shows up twice

## Tech used

- Python
- PostgreSQL (hosted on Render)
- Gemini API (free tier)
- feedparser, BeautifulSoup and youtube-transcript-api for collecting content
- Render for deployment

## Running it locally

You'll need Python 3.11 and a Postgres database. I'm using Render's free one.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(On Mac/Linux, activate with `source .venv/bin/activate` instead.)

Copy `.env.example` to `.env` and add your database URL, plus the API keys once those parts are in. Then run:

```bash
python scripts/run_pipeline.py
```

The tables get created automatically the first time it runs.

## Project structure

```
app/
  main.py        runs the pipeline
  config.py      loads settings from .env
  db/            database schema and connection
  ingestion/     RSS, blog and YouTube fetching
  processing/    summarizing with Gemini
  digest/        building the email
  delivery/      sending the email
scripts/
  run_pipeline.py
```
