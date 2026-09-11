# Signal AI

An autonomous pipeline that monitors AI news sources (RSS feeds, company blogs, YouTube channels), summarizes new content with the OpenAI API, and emails a digest on a schedule.

## Setup

The app runs from a local Python virtual environment and connects to a hosted Postgres database on Render. There is no local database: the same Render instance serves local development and production.

1. In the Render dashboard, create a Postgres database and copy its **External Database URL**.
2. Set up the project:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
   pip install -r requirements.txt
   cp .env.example .env            # then paste the URL into DATABASE_URL
   ```

3. Run one pipeline pass:

   ```bash
   python scripts/run_pipeline.py
   ```

   A successful run logs the Postgres version and a row count for each table.

## Deployment

Planned for phase 8: the cloud service that runs the daily job builds the app from a Dockerfile, so Docker never needs to be installed locally.

## Layout

```
app/
  main.py            entrypoint, runs one pipeline pass
  config.py          loads env vars
  db/                schema.sql (source of truth), models.py, connection helpers
  ingestion/         rss, blogs, youtube            (phases 2-4)
  processing/        markdown + OpenAI summaries    (phase 5)
  digest/            digest assembly                (phase 6)
  delivery/          email send                     (phase 7)
scripts/
  run_pipeline.py    manual trigger
```

The schema is applied on every run (`CREATE TABLE IF NOT EXISTS`), so a fresh database needs no separate setup step.

## Build phases

- [x] 1. Scaffold + schema
- [ ] 2. RSS ingestion
- [ ] 3. Blog monitoring
- [ ] 4. YouTube ingestion
- [ ] 5. Summarization pipeline
- [ ] 6. Digest assembly
- [ ] 7. Email delivery
- [ ] 8. Deploy (cloud build from a Dockerfile)
- [ ] 9. Subscriber list
