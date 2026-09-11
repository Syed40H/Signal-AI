-- Signal AI schema. Idempotent: applied on every pipeline run.

-- Configured sources to monitor
CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    type        TEXT NOT NULL CHECK (type IN ('rss', 'blog', 'youtube')),
    name        TEXT NOT NULL,                      -- display name, e.g. "OpenAI Blog"
    url         TEXT NOT NULL,                      -- feed url, blog url, or channel id
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (type, url)
);

-- Every piece of content pulled from a source
CREATE TABLE IF NOT EXISTS items (
    id                SERIAL PRIMARY KEY,
    source_id         INTEGER NOT NULL REFERENCES sources(id),
    external_id       TEXT NOT NULL,                -- video id / post url / guid, for dedup
    title             TEXT,
    url               TEXT,                         -- link to the original post/video
    raw_content       TEXT,                         -- original transcript/post body
    markdown_content  TEXT,                         -- converted markdown
    summary           TEXT,                         -- LLM-generated summary
    published_at      TIMESTAMPTZ,
    fetched_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent              BOOLEAN NOT NULL DEFAULT FALSE,  -- included in a digest yet?
    UNIQUE (source_id, external_id)
);

-- items.url was added after the first tables were created
ALTER TABLE items ADD COLUMN IF NOT EXISTS url TEXT;

-- One row per digest email actually sent
CREATE TABLE IF NOT EXISTS digests (
    id          SERIAL PRIMARY KEY,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    item_count  INTEGER,
    content     TEXT                                -- full digest body, for your own records
);

-- Recipients (only you at first; real list later)
CREATE TABLE IF NOT EXISTS subscribers (
    id             SERIAL PRIMARY KEY,
    email          TEXT UNIQUE NOT NULL,
    active         BOOLEAN NOT NULL DEFAULT TRUE,
    subscribed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
