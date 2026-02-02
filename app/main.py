# app/main.py — FastAPI app entry; served via uvicorn in Docker (see Dockerfile + docker-compose api service).
from fastapi import Body, FastAPI, Depends, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .db import get_session
from .crawl import crawl_url
import httpx
from .ingest import chunk_text
from .embeddings import embed_texts
from .search import similarity_search
from .reports import build_quarterly_report_markdown
from .openai_websearch import OpenAIWebSearchClient
from .newsletter import build_newsletter_markdown

app = FastAPI(title="Scraper/Aggregator MVP")

# Allow Vite dev server (and other origins) to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

websearch = OpenAIWebSearchClient()

class SourceIn(BaseModel):
    name: str
    base_url: HttpUrl

class CrawlIn(BaseModel):
    url: HttpUrl
    source_id: int | None = None

class DiscoverIn(BaseModel):
    query: str
    instructions: str | None = None
    web_search_options: dict | None = None

class QueryIn(BaseModel):
    query: str
    top_k: int = 10

class ReportIn(BaseModel):
    quarter_label: str
    query: str = "top themes"
    top_k: int = 25


class NewsletterTemplateIn(BaseModel):
    name: str
    system_prompt: str
    source_urls: list[str] = []
    example_content: str | None = None
    use_web_search: bool = True


class NewsletterRunIn(BaseModel):
    label: str
    prompt_override: str | None = None
    extra_source_urls: list[str] = []


class NewsletterRunUpdate(BaseModel):
    label: str | None = None
    prompt_override: str | None = None
    extra_source_urls: list[str] | None = None
    feedback: str | None = None


# Default prompt for /test-websearch: equities newsletter in style of prior quarters.
NEWSLETTER_TEST_PROMPT = """You are to build a newsletter on the equities markets for Q1. Similar to these examples from prior quarters:

Previous reports
Q1 2024
The strong market momentum from 2023 spilled over into the first quarter of this year, as global equity markets marched higher on much better-than-feared economic data, an improving corporate earnings picture, and a continuation of the AI mania that dominated last year's market narrative. The MSCI All-Country World Index (ACWI) of global stocks gained 8.2% for the quarter to finish at a new high-water mark, representing its 21st new record high so far this year.
• The S&P 500 Index logged a 10.6% total return during the first quarter, capping a five-month win streak during which blue chip U.S. stocks advanced 30% off of late October lows and added more than $9 trillion in market value. The index reached a new record high on January 24th, fully erasing the bear market losses from 2022, and the S&P notched 21 more records before quarter end.
Q2 2024
Fueled by a moderating of global inflationary pressure, growing optimism around an easing of financial conditions by central bankers that seems increasingly imminent, and a continuation of the AI-mania that has gripped investors for more than a year, global equity markets continued their hot streak through the second quarter. The MSCI All-Country World Index (ACWI) of global stocks gained 2.9% in Q2, capping an 11.3% total return for the global blue-chip benchmark through mid-year and a near 50% rally since stocks bottomed in late September of 2022.
• The S&P 500 Index logged a 4.3% total return during the second quarter, boosting year-to- date gains to 15.3% and continuing a three-quarter win streak that has added more than $10 trillion in market value. Through Q2, the S&P notched 31 new records highs so far this year.
Q3 2024
Global equity markets enjoyed a strong, broad-based rally during the third quarter, as stronger corporate earnings, better-than-expected economic data, and the official launch of the Federal Reserve's long-awaited rate cutting cycle fueled demand for risk assets. The MSCI All-Country World Index (ACWI) of global stocks gained 6.6% in Q3, bringing year-to-date returns to 18.7%.
• The S&P 500 Index logged a 5.9% total return during the third quarter to boost YTD gains to 22.1%, continuing a four-quarter win streak and capping the best YTD September return for the blue-chip index since 1997. The S&P closed the quarter at a new all-time high, its 43rd record close so far this year.
Q4 2024
Despite a late December sell off, global equity markets gave investors a lot to cheer in 2024, posting a second consecutive year of strong, double-digit returns. The MSCI All-Country World Index (ACWI) of global stocks retreated 1.0% in Q4, but the index still posted a full-year total return of 17.5% to extend the current bull market past the two-year mark.
• The S&P 500 Index logged a 2.4% total return during the fourth quarter to boost full-year gains to 25.0%, continuing a five-quarter win streak and capping the best two-year return (57.9%) for the blue-chip index since 1997-98.
• The S&P hit 57 new record highs and added $10 trillion in market value in 2024.
Q1 2025
The first quarter was a tale of two halves for the global equity markets.  Building on the strong momentum of the prior two years, the MSCI All-Country World Index (ACWI) surged nearly 6% and hit multiple record highs during the first six weeks of 2025, but a steady selloff in risk assets erased those gains and more by quarter's end.    When the dust settled, global stocks suffered a modest 1.3% loss for the quarter, but this reversal set the stage for the much sharper correction in stocks we have experienced in early April following the announcement of the Trump administration's aggressive global tariff program.
• After a fast start culminating in the Index's third new record high of the year on February 19th, the S&P 500 Index corrected more than 10% by mid March to record a first quarter loss of 4.3%, snapping a five-quarter win streak for U.S. blue chip stocks.
Q2 2025
Following the announcement of Trump's harsher-than-expected tariff policy, global stocks suffered one of their worst three day drops in history before fully recovering to reach new record highs by quarter's end. After dropping more than 10% during this stretch to flirt with bear market territory, the MSCI All-Country World Index (ACWI) rebounded to post second quarter and year-to-date returns of 11.5% and 10.1%, respectively, to close the first half at its seventeenth new record high so far this year.
• U.S. stocks followed a similar pattern, as the S&P 500 declined 18.9% between its record high on February 19th and its early April lows, only to finish the second quarter at new record highs. Q2 and YTD returns for the blue-chip index were 10.9% and 6.2%, respectively.
• Just five stocks drove 55% of the S&P's Q2 return, led by strong gains in mega caps NVIDIA (+46%), Microsoft (+33%), Broadcom (+65%), Meta (+28%), and Amazon (+15%).

Use web search to find current Q1 2026 (or latest available) equities data and write the next newsletter section in the same style and format."""

class TestWebSearchIn(BaseModel):
    """Optional override for /test-websearch; if omitted, uses default newsletter prompt."""
    query: str | None = None
    instructions: str | None = None

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/sources")
async def create_source(payload: SourceIn, session: AsyncSession = Depends(get_session)):
    q = text("INSERT INTO sources(name, base_url) VALUES (:n, :u) RETURNING id")
    sid = (await session.execute(q, {"n": payload.name, "u": str(payload.base_url)})).scalar_one()
    await session.commit()
    return {"id": sid}

@app.post("/discover")
async def discover(payload: DiscoverIn):
    instructions = payload.instructions or (
        "Search the web for relevant sources. "
        "Return: (1) a short summary, (2) a list of 10-20 candidate sources "
        "with title, publisher, date if available, and why it’s useful. "
        "Prefer primary sources (official reports, PDFs, investor letters). "
        "Include URLs."
    )
    r = websearch.search(payload.query, instructions=instructions, web_search_options=payload.web_search_options)
    # NOTE: parsing URLs from the answer is intentionally left to a follow-up step
    # (you'll likely want a structured extraction pass + dedupe logic).
    return {"answer_markdown": r.answer_markdown, "raw": r.raw_response}

# Crawl a URL via Crawl4AI Docker container; store doc + chunks + embeddings.
@app.post("/crawl")
async def crawl(payload: CrawlIn, session: AsyncSession = Depends(get_session)):
    await session.execute(text("""
      INSERT INTO crawl_runs(source_id, url, status)
      VALUES (:sid, :url, 'started')
    """), {"sid": payload.source_id, "url": str(payload.url)})
    await session.commit()

    try:
        data = await crawl_url(str(payload.url))
    except httpx.HTTPStatusError as e:
        err_msg = str(e.response.status_code) + " " + (e.response.reason_phrase or "")
        if e.response.status_code == 403:
            err_msg = "PDF URL returned 403 Forbidden; host may require a browser. Try a public PDF (e.g. https://arxiv.org/pdf/2310.06825.pdf) to validate."
        await session.execute(text("""
          INSERT INTO crawl_runs(source_id, url, status, error)
          VALUES (:sid, :url, 'failed', :err)
        """), {"sid": payload.source_id, "url": str(payload.url), "err": err_msg})
        await session.commit()
        raise HTTPException(400, err_msg)
    if not data["markdown"]:
        await session.execute(text("""
          INSERT INTO crawl_runs(source_id, url, status, error)
          VALUES (:sid, :url, 'failed', :err)
        """), {"sid": payload.source_id, "url": data["url"], "err": "No content extracted"})
        await session.commit()
        raise HTTPException(400, "No content extracted.")

    ins_doc = text("""
      INSERT INTO documents(source_id, url, title, content_markdown, content_hash)
      VALUES (:sid, :url, :title, :md, :h)
      ON CONFLICT (url, content_hash) DO NOTHING
      RETURNING id
    """)
    doc_id = (await session.execute(ins_doc, {
        "sid": payload.source_id,
        "url": data["url"],
        "title": data["title"],
        "md": data["markdown"],
        "h": data["content_hash"],
    })).scalar_one_or_none()

    if doc_id is None:
        doc_id = (await session.execute(
            text("SELECT id FROM documents WHERE url=:url AND content_hash=:h ORDER BY id DESC LIMIT 1"),
            {"url": data["url"], "h": data["content_hash"]}
        )).scalar_one()

    chunks = chunk_text(data["markdown"])
    vectors = await embed_texts(chunks)

    for idx, (ch, vec) in enumerate(zip(chunks, vectors)):
        vec_literal = "[" + ",".join(str(x) for x in vec) + "]"
        await session.execute(text("""
          INSERT INTO chunks(document_id, url, chunk_index, content, embedding)
          VALUES (:did, :url, :i, :c, CAST(:e AS vector))
          ON CONFLICT (document_id, chunk_index) DO NOTHING
        """), {"did": doc_id, "url": data["url"], "i": idx, "c": ch, "e": vec_literal})

    await session.execute(text("""
      INSERT INTO crawl_runs(source_id, url, status)
      VALUES (:sid, :url, 'success')
    """), {"sid": payload.source_id, "url": data["url"]})
    await session.commit()
    return {"document_id": doc_id, "chunks": len(chunks)}

# Test OpenAI web search with newsletter prompt (default) or custom query/instructions.
@app.post("/test-websearch")
async def test_websearch(payload: TestWebSearchIn | None = Body(None)):
    if payload and (payload.query or payload.instructions):
        query = payload.query or "Summarize current equities market conditions."
        instructions = payload.instructions or "Use web search. Be concise."
    else:
        query = NEWSLETTER_TEST_PROMPT
        instructions = (
            "You are a financial newsletter writer. Use web search to find the latest quarterly "
            "equities data (Q1 2026 or most recent). Write the next newsletter section in the same "
            "style, format, and level of detail as the previous reports. Include MSCI ACWI and "
            "S&P 500 returns and key narrative points."
        )
    r = websearch.search(query, instructions=instructions)
    return {"answer_markdown": r.answer_markdown, "raw": r.raw_response}

# Same as /test-websearch but accepts form data so multi-line query/instructions work without JSON escaping.
@app.post("/test-websearch/form")
async def test_websearch_form(
    query: str | None = Form(None),
    instructions: str | None = Form(None),
):
    if query and query.strip():
        q = query.strip()
        inst = (instructions or "Use web search. Be concise.").strip()
    elif instructions and instructions.strip():
        q = "Summarize current equities market conditions."
        inst = instructions.strip()
    else:
        q = NEWSLETTER_TEST_PROMPT
        inst = (
            "You are a financial newsletter writer. Use web search to find the latest quarterly "
            "equities data (Q1 2026 or most recent). Write the next newsletter section in the same "
            "style, format, and level of detail as the previous reports. Include MSCI ACWI and "
            "S&P 500 returns and key narrative points."
        )
    r = websearch.search(q, instructions=inst)
    return {"answer_markdown": r.answer_markdown, "raw": r.raw_response}

@app.post("/query")
async def query(payload: QueryIn, session: AsyncSession = Depends(get_session)):
    qvec = (await embed_texts([payload.query]))[0]
    rows = await similarity_search(session, qvec, limit=payload.top_k)
    return {"matches": rows}

@app.post("/report")
async def report(payload: ReportIn, session: AsyncSession = Depends(get_session)):
    qvec = (await embed_texts([payload.query]))[0]
    matches = await similarity_search(session, qvec, limit=payload.top_k)
    md = build_quarterly_report_markdown(payload.quarter_label, matches)
    return {"report_markdown": md, "sources_used": list({m["url"] for m in matches})}


# --- Newsletter templates and runs ---

@app.get("/newsletter-templates")
async def list_newsletter_templates(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(text("""
        SELECT id, name, system_prompt, source_urls, example_content, use_web_search, created_at
        FROM newsletter_templates ORDER BY created_at DESC
    """))).mappings().all()
    return {"templates": [dict(r) for r in rows]}


@app.post("/newsletter-templates")
async def create_newsletter_template(payload: NewsletterTemplateIn, session: AsyncSession = Depends(get_session)):
    import json
    q = text("""
        INSERT INTO newsletter_templates(name, system_prompt, source_urls, example_content, use_web_search)
        VALUES (:name, :system_prompt, :source_urls, :example_content, :use_web_search)
        RETURNING id, name, system_prompt, source_urls, example_content, use_web_search, created_at
    """)
    row = (await session.execute(q, {
        "name": payload.name,
        "system_prompt": payload.system_prompt,
        "source_urls": json.dumps(payload.source_urls),
        "example_content": payload.example_content,
        "use_web_search": payload.use_web_search,
    })).mappings().one()
    await session.commit()
    return dict(row)


@app.get("/newsletter-templates/{template_id}")
async def get_newsletter_template(template_id: int, session: AsyncSession = Depends(get_session)):
    row = (await session.execute(text("""
        SELECT id, name, system_prompt, source_urls, example_content, use_web_search, created_at
        FROM newsletter_templates WHERE id = :id
    """), {"id": template_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Template not found")
    return dict(row)


@app.put("/newsletter-templates/{template_id}")
async def update_newsletter_template(template_id: int, payload: NewsletterTemplateIn, session: AsyncSession = Depends(get_session)):
    import json
    r = (await session.execute(text("SELECT id FROM newsletter_templates WHERE id = :id"), {"id": template_id})).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Template not found")
    await session.execute(text("""
        UPDATE newsletter_templates
        SET name = :name, system_prompt = :system_prompt, source_urls = :source_urls, example_content = :example_content, use_web_search = :use_web_search
        WHERE id = :id
    """), {
        "id": template_id,
        "name": payload.name,
        "system_prompt": payload.system_prompt,
        "source_urls": json.dumps(payload.source_urls),
        "example_content": payload.example_content,
        "use_web_search": payload.use_web_search,
    })
    await session.commit()
    return await get_newsletter_template(template_id, session)


@app.delete("/newsletter-templates/{template_id}")
async def delete_newsletter_template(template_id: int, session: AsyncSession = Depends(get_session)):
    r = (await session.execute(text("DELETE FROM newsletter_templates WHERE id = :id RETURNING id"), {"id": template_id})).scalar_one_or_none()
    await session.commit()
    if not r:
        raise HTTPException(404, "Template not found")
    return {"deleted": True, "id": template_id}


@app.get("/newsletter-templates/{template_id}/runs")
async def list_newsletter_runs(template_id: int, session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(text("""
        SELECT id, template_id, label, prompt_override, extra_source_urls, feedback, report_markdown IS NOT NULL AS has_report, created_at, updated_at
        FROM newsletter_runs WHERE template_id = :tid ORDER BY updated_at DESC
    """), {"tid": template_id})).mappings().all()
    return {"runs": [dict(r) for r in rows]}


@app.post("/newsletter-templates/{template_id}/runs")
async def create_newsletter_run(template_id: int, payload: NewsletterRunIn, session: AsyncSession = Depends(get_session)):
    import json
    # Ensure template exists
    t = (await session.execute(text("SELECT id FROM newsletter_templates WHERE id = :id"), {"id": template_id})).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Template not found")
    q = text("""
        INSERT INTO newsletter_runs(template_id, label, prompt_override, extra_source_urls)
        VALUES (:tid, :label, :prompt_override, :extra_source_urls)
        RETURNING id, template_id, label, prompt_override, extra_source_urls, created_at, updated_at
    """)
    row = (await session.execute(q, {
        "tid": template_id,
        "label": payload.label,
        "prompt_override": payload.prompt_override,
        "extra_source_urls": json.dumps(payload.extra_source_urls),
    })).mappings().one()
    await session.commit()
    return dict(row)


@app.get("/newsletter-runs/{run_id}")
async def get_newsletter_run(run_id: int, session: AsyncSession = Depends(get_session)):
    row = (await session.execute(text("""
        SELECT r.id, r.template_id, r.label, r.prompt_override, r.extra_source_urls, r.feedback, r.report_markdown, r.created_at, r.updated_at,
               t.name AS template_name, t.system_prompt, t.example_content, t.use_web_search
        FROM newsletter_runs r
        JOIN newsletter_templates t ON t.id = r.template_id
        WHERE r.id = :id
    """), {"id": run_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Run not found")
    return dict(row)


@app.put("/newsletter-runs/{run_id}")
async def update_newsletter_run(run_id: int, payload: NewsletterRunUpdate, session: AsyncSession = Depends(get_session)):
    import json
    row = (await session.execute(text("SELECT id, template_id FROM newsletter_runs WHERE id = :id"), {"id": run_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Run not found")
    updates = []
    params = {"id": run_id}
    if payload.label is not None:
        updates.append("label = :label")
        params["label"] = payload.label
    if payload.prompt_override is not None:
        updates.append("prompt_override = :prompt_override")
        params["prompt_override"] = payload.prompt_override
    if payload.extra_source_urls is not None:
        updates.append("extra_source_urls = :extra_source_urls")
        params["extra_source_urls"] = json.dumps(payload.extra_source_urls)
    if payload.feedback is not None:
        updates.append("feedback = :feedback")
        params["feedback"] = payload.feedback
    if updates:
        updates.append("updated_at = NOW()")
        await session.execute(text(f"UPDATE newsletter_runs SET {', '.join(updates)} WHERE id = :id"), params)
        await session.commit()
    return await get_newsletter_run(run_id, session)


@app.delete("/newsletter-runs/{run_id}")
async def delete_newsletter_run(run_id: int, session: AsyncSession = Depends(get_session)):
    r = (await session.execute(text("DELETE FROM newsletter_runs WHERE id = :id RETURNING id"), {"id": run_id})).scalar_one_or_none()
    await session.commit()
    if not r:
        raise HTTPException(404, "Run not found")
    return {"deleted": True, "id": run_id}


@app.post("/newsletter-runs/{run_id}/generate")
async def generate_newsletter_run(run_id: int, session: AsyncSession = Depends(get_session)):
    """Optionally crawl extra_source_urls, then build newsletter from template + RAG + optional web search."""
    import json
    row = (await session.execute(text("""
        SELECT r.id, r.template_id, r.label, r.prompt_override, r.extra_source_urls, r.feedback,
               t.system_prompt, t.example_content, t.use_web_search
        FROM newsletter_runs r
        JOIN newsletter_templates t ON t.id = r.template_id
        WHERE r.id = :id
    """), {"id": run_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Run not found")
    extra_urls = json.loads(row["extra_source_urls"]) if isinstance(row["extra_source_urls"], str) else (row["extra_source_urls"] or [])
    # Crawl any extra URLs so they enter RAG (source_id=None)
    for url in extra_urls:
        if not url or not str(url).strip().startswith(("http://", "https://")):
            continue
        try:
            data = await crawl_url(str(url).strip())
            if data.get("markdown"):
                doc_id = (await session.execute(text("""
                    INSERT INTO documents(source_id, url, title, content_markdown, content_hash)
                    VALUES (NULL, :url, :title, :md, :h)
                    ON CONFLICT (url, content_hash) DO NOTHING RETURNING id
                """), {"url": data["url"], "title": data["title"], "md": data["markdown"], "h": data["content_hash"]})).scalar_one_or_none()
                if doc_id is None:
                    doc_id = (await session.execute(
                        text("SELECT id FROM documents WHERE url=:url AND content_hash=:h ORDER BY id DESC LIMIT 1"),
                        {"url": data["url"], "h": data["content_hash"]}
                    )).scalar_one()
                chunks = chunk_text(data["markdown"])
                vectors = await embed_texts(chunks)
                for idx, (ch, vec) in enumerate(zip(chunks, vectors)):
                    vec_literal = "[" + ",".join(str(x) for x in vec) + "]"
                    await session.execute(text("""
                        INSERT INTO chunks(document_id, url, chunk_index, content, embedding)
                        VALUES (:did, :url, :i, :c, CAST(:e AS vector))
                        ON CONFLICT (document_id, chunk_index) DO NOTHING
                    """), {"did": doc_id, "url": data["url"], "i": idx, "c": ch, "e": vec_literal})
        except Exception:
            pass  # continue with other URLs and RAG
    await session.commit()

    md = await build_newsletter_markdown(
        session,
        system_prompt=row["system_prompt"],
        example_content=row.get("example_content"),
        run_label=row["label"],
        prompt_override=row.get("prompt_override"),
        feedback=row.get("feedback"),
        use_web_search=row["use_web_search"],
    )
    await session.execute(text("""
        UPDATE newsletter_runs SET report_markdown = :md, updated_at = NOW() WHERE id = :id
    """), {"md": md, "id": run_id})
    await session.commit()
    return {"report_markdown": md}
