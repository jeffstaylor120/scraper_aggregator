from dataclasses import dataclass
from typing import Any, Dict, Optional
from openai import OpenAI
from .settings import settings

@dataclass
class WebSearchResult:
    answer_markdown: str
    raw_response: Dict[str, Any]

class OpenAIWebSearchClient:
    """
    Discovery module: use OpenAI's built-in web_search tool to find candidate sources.
    Persist discovered URLs into your DB, then crawl with Crawl4AI for durable ingestion.
    """
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def search(self, query: str, instructions: str = "Find primary sources and list URLs.", web_search_options: Optional[Dict[str, Any]] = None) -> WebSearchResult:
        # Responses API (openai>=2.x): instructions=system, input=user message, tools=[web_search]
        tool = {"type": "web_search"}
        if web_search_options:
            tool.update(web_search_options)

        resp = self.client.responses.create(
            model=settings.openai_model,
            instructions=instructions,
            input=query,
            tools=[tool],
        )
        raw = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
        return WebSearchResult(
            answer_markdown=getattr(resp, "output_text", "") or "",
            raw_response=raw,
        )
