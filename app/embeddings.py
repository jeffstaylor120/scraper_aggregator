from openai import OpenAI
from .settings import settings

_client = OpenAI(api_key=settings.openai_api_key)

async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Returns embeddings for each input string.
    Note: OpenAI SDK call is synchronous; for strict async you can wrap in a thread executor.
    """
    resp = _client.embeddings.create(
        model=settings.openai_embed_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]
