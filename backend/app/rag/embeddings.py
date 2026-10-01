import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768


def _get_client() -> genai.Client:
    api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured."
        )

    return genai.Client(
        api_key=api_key
    )


def _embed_documents_sync(
    texts: list[str],
) -> list[list[float]]:

    client = _get_client()

    contents = [
        types.Content(
            parts=[
                types.Part.from_text(
                    text=(
                        f"title: LocalGPT document chunk | "
                        f"text: {text}"
                    )
                )
            ]
        )
        for text in texts
    ]

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=contents,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    return [
        list(embedding.values)
        for embedding in response.embeddings
    ]


async def embed_documents(
    texts: list[str],
) -> list[list[float]]:

    if not texts:
        return []

    return await asyncio.to_thread(
        _embed_documents_sync,
        texts,
    )


def _embed_query_sync(
    query: str,
) -> list[float]:

    client = _get_client()

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=(
            "task: search result | "
            f"query: {query}"
        ),
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    return list(
        response.embeddings[0].values
    )


async def embed_query(
    query: str,
) -> list[float]:

    return await asyncio.to_thread(
        _embed_query_sync,
        query,
    )