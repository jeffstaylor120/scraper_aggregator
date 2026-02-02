# app/newsletter.py — newsletter generation: template system prompt + RAG + optional web search.
from openai import OpenAI

from .settings import settings
from .embeddings import embed_texts
from .search import similarity_search
from .openai_websearch import OpenAIWebSearchClient

_client = OpenAI(api_key=settings.openai_api_key)
_websearch = OpenAIWebSearchClient()


async def build_newsletter_markdown(
    session,
    *,
    system_prompt: str,
    example_content: str | None,
    run_label: str,
    prompt_override: str | None = None,
    feedback: str | None = None,
    rag_top_k: int = 25,
    rag_query: str | None = None,
    use_web_search: bool = True,
    web_search_query: str | None = None,
    web_search_instructions: str | None = None,
) -> str:
    """
    Build newsletter body: system_prompt (+ prompt_override) + example + RAG context + optional web search.
    """
    query_embed = rag_query or f"quarterly market review {run_label}"
    qvec = (await embed_texts([query_embed]))[0]
    matches = await similarity_search(session, qvec, limit=rag_top_k)
    rag_context = "\n\n".join(
        f"- URL: {m['url']}\n  score: {m.get('score', '')}\n  excerpt: {m['content']}"
        for m in matches
    )

    web_md = ""
    if use_web_search:
        q = web_search_query or f"Q4 2025 and Q1 2026 market commentary, equities, fixed income, {run_label}"
        inst = web_search_instructions or (
            "Find recent quarterly market commentary and key metrics (index returns, Fed, etc.). "
            "Be concise; prefer primary sources."
        )
        r = _websearch.search(q, instructions=inst)
        web_md = (r.answer_markdown or "").strip()

    user_prompt = f"Create a newsletter for: **{run_label}**.\n\n"
    if prompt_override and prompt_override.strip():
        user_prompt += f"Additional instructions for this run:\n{prompt_override.strip()}\n\n"
    if feedback and feedback.strip():
        user_prompt += f"User feedback (apply when revising):\n{feedback.strip()}\n\n"
    user_prompt += "Use ONLY the following context (RAG excerpts and optional web search). "
    user_prompt += "Structure: 1) Executive Summary 2) Themes & Developments 3) Notable Sources (with URLs) 4) Risks & Watchlist.\n\n"
    user_prompt += "--- RAG EXCERPTS (from crawled docs) ---\n"
    user_prompt += rag_context or "(none)"
    if web_md:
        user_prompt += "\n\n--- WEB SEARCH RESULT ---\n"
        user_prompt += web_md
    user_prompt += "\n\n--- END CONTEXT ---"

    system = system_prompt.strip()
    if example_content and example_content.strip():
        system += "\n\n--- EXAMPLE NEWSLETTER STYLE/CONTENT (match tone and structure) ---\n"
        system += example_content.strip()
        system += "\n--- END EXAMPLE ---"

    resp = _client.responses.create(
        model=settings.openai_model,
        instructions=system,
        input=user_prompt,
    )
    return getattr(resp, "output_text", "") or ""
