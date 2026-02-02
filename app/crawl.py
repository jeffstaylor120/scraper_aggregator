# app/crawl.py — calls Crawl4AI Docker container HTTP API; returns normalized content.
# PDFs: Crawl4AI Docker API fails (dict/logger) with PDF strategies; we use local pypdf extraction.
import hashlib
import io
import re
from urllib.parse import urlparse

import httpx
from pypdf import PdfReader

from .settings import settings

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _is_pdf_url(url: str) -> bool:
    """True if URL looks like a PDF (path ends with .pdf or query has .pdf)."""
    u = (url or "").strip().lower()
    if ".pdf" not in u:
        return False
    try:
        path = u.split("?")[0].split("#")[0]
        return path.endswith(".pdf") or "/.pdf" in path
    except Exception:
        return False


# Browser-like headers so PDF hosts don't block server requests (403)
def _pdf_headers_for(url: str) -> dict:
    p = urlparse(url)
    origin = f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else url
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,*/*",
        "Referer": origin + "/",
    }


async def _crawl_pdf_local(url: str) -> dict:
    """
    Fetch PDF and extract text with pypdf (Crawl4AI Docker PDF API has dict/logger bugs).
    Returns same shape as crawl_url: {url, title, markdown, content_hash}.
    """
    headers = _pdf_headers_for(url)
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True, headers=headers) as client:
        resp = await client.get(url)
        # Some hosts (e.g. dadavidson.com) return 403 for non-browser; surface clear error
        if resp.status_code == 403:
            raise httpx.HTTPStatusError(
                "PDF URL returned 403 Forbidden; host may require a browser. Try a public PDF (e.g. https://arxiv.org/pdf/2310.06825.pdf) to validate.",
                request=resp.request,
                response=resp,
            )
        resp.raise_for_status()
        raw = resp.content
    if not raw:
        return {"url": url, "title": None, "markdown": "", "content_hash": sha256_text("")}
    reader = PdfReader(io.BytesIO(raw))
    parts = []
    for page in reader.pages:
        try:
            t = page.extract_text()
            if t:
                parts.append(t.strip())
        except Exception:
            continue
    # Optional: use PDF metadata as title
    title = None
    try:
        meta = reader.metadata
        if meta and meta.get("/Title"):
            title = meta.get("/Title")
    except Exception:
        pass
    if not title and parts:
        # First non-empty line as fallback title
        first = parts[0][:200] if parts[0] else ""
        first = re.sub(r"\s+", " ", first).strip()
        if first:
            title = first
    markdown = "\n\n".join(parts).strip()
    return {
        "url": url,
        "title": title,
        "markdown": markdown,
        "content_hash": sha256_text(markdown),
    }


async def crawl_url(url: str) -> dict:
    """
    Crawl a single URL. PDFs: local pypdf extraction (Crawl4AI PDF API broken in Docker).
    HTML: Crawl4AI Docker API (POST /crawl). Returns: {url, title, markdown, content_hash}
    """
    if _is_pdf_url(url):
        return await _crawl_pdf_local(url)

    base = settings.crawl4ai_base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{base}/crawl",
            json={"urls": [url]},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results") or []
    if not results:
        return {
            "url": url,
            "title": None,
            "markdown": "",
            "content_hash": sha256_text(""),
        }
    r = results[0]
    raw_md = r.get("markdown")
    if isinstance(raw_md, str):
        md = raw_md.strip()
    elif isinstance(raw_md, dict):
        # Crawl4AI 0.8 returns markdown as {raw_markdown, markdown_with_citations, ...}
        md = (
            raw_md.get("raw_markdown")
            or raw_md.get("markdown_with_citations")
            or raw_md.get("content")
            or raw_md.get("text")
            or ""
        ).strip()
    else:
        md = (raw_md or "").__str__().strip() if raw_md is not None else ""
    return {
        "url": r.get("url") or url,
        "title": r.get("title"),
        "markdown": md,
        "content_hash": sha256_text(md),
    }
