from uuid import UUID, uuid4

from psycopg import AsyncConnection
from pgvector import Vector
from pgvector.psycopg import register_vector_async

from app.rag.embeddings import embed_documents
from app.rag.parser import extract_text
from app.rag.chunker import chunk_text


MAX_DOCUMENT_SIZE = 10 * 1024 * 1024

MAX_CHUNKS_PER_DOCUMENT = 1000


async def ingest_document(
    database_url: str,
    user_id: UUID,
    filename: str,
    content_type: str,
    content: bytes,
) -> dict:

    if len(content) > MAX_DOCUMENT_SIZE:
        raise ValueError(
            "Document is too large. "
            "Maximum allowed size is 10 MB."
        )

    text = extract_text(
        filename,
        content,
    )

    if not text.strip():
        raise ValueError(
            "The document does not contain extractable text."
        )

    chunks = chunk_text(text)

    if not chunks:
        raise ValueError(
            "No usable text chunks were created."
        )

    if len(chunks) > MAX_CHUNKS_PER_DOCUMENT:
        raise ValueError(
            "The document contains too much text "
            "for a single upload."
        )

    embeddings = await embed_documents(
        chunks
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match "
            "chunk count."
        )

    document_id = uuid4()

    async with await AsyncConnection.connect(
        database_url
    ) as connection:

        await register_vector_async(
            connection
        )

        async with connection.transaction():

            await connection.execute(
                """
                INSERT INTO documents (
                    id,
                    user_id,
                    filename,
                    content_type,
                    size_bytes
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    document_id,
                    user_id,
                    filename,
                    content_type,
                    len(content),
                ),
            )

            for index, (
                chunk,
                embedding,
            ) in enumerate(
                zip(
                    chunks,
                    embeddings,
                )
            ):

                await connection.execute(
                    """
                    INSERT INTO document_chunks (
                        id,
                        document_id,
                        user_id,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        uuid4(),
                        document_id,
                        user_id,
                        index,
                        chunk,
                        Vector(embedding),
                    ),
                )

    return {
        "document_id": str(document_id),
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(content),
        "chunk_count": len(chunks),
    }


async def list_documents(
    database_url: str,
    user_id: UUID,
) -> list[dict]:

    async with await AsyncConnection.connect(
        database_url
    ) as connection:

        cursor = await connection.execute(
            """
            SELECT
                id,
                filename,
                content_type,
                size_bytes,
                created_at
            FROM documents
            WHERE user_id = %s
            ORDER BY created_at DESC;
            """,
            (user_id,),
        )

        rows = await cursor.fetchall()

    return [
        {
            "id": str(row[0]),
            "filename": row[1],
            "content_type": row[2],
            "size_bytes": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


async def delete_document(
    database_url: str,
    user_id: UUID,
    document_id: UUID,
) -> bool:

    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:

        result = await connection.execute(
            """
            DELETE FROM documents
            WHERE id = %s
            AND user_id = %s;
            """,
            (
                document_id,
                user_id,
            ),
        )

    return result.rowcount > 0