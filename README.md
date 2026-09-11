# Signal AI

An autonomous pipeline that monitors AI news sources (RSS feeds, company blogs, YouTube channels), summarizes new content with the OpenAI API, and emails a digest on a schedule.

## Quick start (Docker)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env
docker compose up --build
```

This starts Postgres, applies the schema, and runs one pipeline pass. The `app` container exits when the run finishes; `db` keeps running.

## Local development (Python on your machine, Postgres in Docker)

```bash
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env
python scripts/run_pipeline.py
```

A successful run logs the Postgres version and a row count for each table.

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
- [ ] 8. Dockerize fully
- [ ] 9. Deploy to Render
- [ ] 10. Subscriber list
