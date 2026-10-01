from uuid import UUID

from psycopg import AsyncConnection
from pgvector import Vector
from pgvector.psycopg import register_vector_async

from app.rag.embeddings import embed_query


async def search_documents(
    database_url: str,
    user_id: UUID,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Search the current user's uploaded document chunks
    using pgvector cosine similarity.
    """

    query = query.strip()

    if not query:
        return []

    # Keep tool usage reasonable.
    top_k = max(1, min(top_k, 10))

    query_embedding = await embed_query(query)

    async with await AsyncConnection.connect(database_url) as connection:
        await register_vector_async(connection)

        cursor = await connection.execute(
            """
            SELECT
                dc.id,
                dc.document_id,
                d.filename,
                dc.chunk_index,
                dc.content,
                1 - (dc.embedding <=> %s) AS similarity
            FROM document_chunks dc
            INNER JOIN documents d
                ON d.id = dc.document_id
            WHERE dc.user_id = %s
            ORDER BY dc.embedding <=> %s
            LIMIT %s;
            """,
            (
                Vector(query_embedding),
                user_id,
                Vector(query_embedding),
                top_k,
            ),
        )

        rows = await cursor.fetchall()

    return [
        {
            "chunk_id": str(row[0]),
            "document_id": str(row[1]),
            "filename": row[2],
            "chunk_index": row[3],
            "content": row[4],
            "similarity": float(row[5]),
        }
        for row in rows
    ]