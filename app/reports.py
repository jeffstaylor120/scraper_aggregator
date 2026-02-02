from openai import OpenAI
from .settings import settings

_client = OpenAI(api_key=settings.openai_api_key)

def build_quarterly_report_markdown(quarter_label: str, context_snippets: list[dict]) -> str:
    """
    Generates a quarterly report using ONLY your stored snippets (deterministic + auditable).
    """
    context = "\n\n".join(
        f"- URL: {s['url']}\n  score: {s.get('score','')}\n  excerpt: {s['content']}"
        for s in context_snippets
    )

    prompt = f"""
Create a quarterly report for {quarter_label}.

Use ONLY the provided excerpts. Structure:
1) Executive Summary
2) Themes & Developments
3) Notable Sources (with URLs)
4) Risks & Watchlist
5) Appendix: bullet list of sources

EXCERPTS:
{context}
""".strip()

    resp = _client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )
    return getattr(resp, "output_text", "")
