from psycopg import AsyncConnection


EMBEDDING_DIMENSIONS = 768


async def setup_rag_tables(
    database_url: str,
) -> None:
    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:

        # Enable pgvector.
        await connection.execute(
            """
            CREATE EXTENSION IF NOT EXISTS vector;
            """
        )

        # Store uploaded document metadata.
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,

                user_id UUID NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                filename TEXT NOT NULL,

                content_type TEXT NOT NULL,

                size_bytes BIGINT NOT NULL,

                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT NOW()
            );
            """
        )

        # Store document chunks and embeddings.
        await connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id UUID PRIMARY KEY,

                document_id UUID NOT NULL
                    REFERENCES documents(id)
                    ON DELETE CASCADE,

                user_id UUID NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                chunk_index INTEGER NOT NULL,

                content TEXT NOT NULL,

                embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,

                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT NOW(),

                UNIQUE (
                    document_id,
                    chunk_index
                )
            );
            """
        )

        # User filtering.
        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_documents_user_id
            ON documents(user_id);
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_document_chunks_user_id
            ON document_chunks(user_id);
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_document_chunks_document_id
            ON document_chunks(document_id);
            """
        )

        # Vector similarity index.
        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_document_chunks_embedding_hnsw
            ON document_chunks
            USING hnsw (
                embedding vector_cosine_ops
            );
            """
        )