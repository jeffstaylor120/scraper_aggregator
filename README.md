# Scraper / Aggregator MVP (Step 1)

This project is the first step toward a **generic web scraper + source aggregator** that:
- discovers candidate sources on the open web (OpenAI web search)
- crawls & extracts durable content (Crawl4AI / Playwright)
- stores raw content in Postgres
- chunks + embeds content
- stores embeddings in **pgvector** (vector store inside Postgres)
- supports semantic search + report generation (OpenAI)

## Features included (Step 1)

### Discovery (OpenAI Web Search)
- `POST /discover`
  - Uses OpenAI **Responses API** with the `web_search` tool to find relevant sources and return an answer containing candidate URLs and notes.
  - Intended for **source discovery** (find candidates), not durable archiving.

### Durable ingestion (Crawl4AI)
- `POST /crawl`
  - Crawls a URL using Crawl4AI (Playwright/Chromium in Docker)
  - Stores:
    - `documents` (markdown + content hash)
    - `chunks` (chunked text + embeddings)
    - `crawl_runs` audit records

### Vector search (pgvector)
- `POST /query`
  - Embeds the query with OpenAI embeddings
  - Runs similarity search against stored chunks using pgvector distance ops

### Quarterly report
- `POST /report`
  - Performs semantic retrieval from your stored corpus
  - Generates a markdown report using OpenAI **from your stored excerpts**
  - Returns the report + list of source URLs used

## End goal (what this scaffold is building toward)

A full “scrape + aggregate + report” platform that supports:

1. **Source discovery pipelines**
   - periodic queries
   - structured URL extraction
   - dedupe + canonicalization

2. **Source crawling pipelines**
   - per-source rules (domains, paths, depth, rate limits)
   - recrawl schedules
   - content change detection

3. **Knowledge store**
   - raw snapshots
   - chunking strategies
   - embeddings + metadata filters
   - hybrid search (BM25/trgm + vectors)

4. **Report automation**
   - generate quarterly reports on a schedule
   - traceability: every claim links back to stored sources/snippets
   - export to PDF/Doc/Notion later

## Run locally (Docker)

1) Create `.env`:

```bash
cp .env.example .env
# set OPENAI_API_KEY
```

2) Start:

```bash
docker compose up --build
```

API runs at: http://localhost:8000

## Quick test

### 1) Create a source
```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"Example","base_url":"https://example.com"}'
```

### 2) Discover sources (web search)
```bash
curl -X POST http://localhost:8000/discover \
  -H "Content-Type: application/json" \
  -d '{"query":"Q4 2025 quarterly market commentary PDF site:.com"}'
```

### 3) Crawl a URL (durable ingestion)
```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

### 4) Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"what are the key themes?", "top_k": 5}'
```

### 5) Report
```bash
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d '{"quarter_label":"Q1 2026", "query":"macro, rates, equities", "top_k": 25}'
```

## Notes / next iteration ideas

- Add `/discover_and_register` that:
  - runs web search
  - extracts URLs into a structured list
  - upserts them into `sources` with metadata
- Add `/crawl_source/{id}` and `/crawl_many`
- Add scheduling (Celery/Prefect/APScheduler) to run crawls daily and reports quarterly
- Add ANN indexes (HNSW/IVFFlat) once corpus grows
