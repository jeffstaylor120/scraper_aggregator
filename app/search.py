from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def similarity_search(
    session: AsyncSession,
    query_embedding: list[float],
    limit: int = 10,
):
    vec_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"
    sql = text("""
        SELECT
          url,
          chunk_index,
          content,
          1 - (embedding <=> CAST(:qvec AS vector)) AS score
        FROM chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :limit
    """)
    rows = (await session.execute(sql, {"qvec": vec_literal, "limit": limit})).mappings().all()
    return list(rows)
