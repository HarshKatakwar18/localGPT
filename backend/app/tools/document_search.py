from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.rag.retriever import search_documents


@tool
async def document_search(
    query: str,
    config: RunnableConfig,
) -> str:
    """
    Search the user's uploaded documents for information relevant
    to the user's question.
    """

    user_id = config.get("configurable", {}).get("user_id")
    database_url = config.get("configurable", {}).get("database_url")

    if not user_id:
        return "Document search is unavailable because the user could not be identified."

    if not database_url:
        return "Document search is unavailable because the database configuration is missing."

    try:
        user_uuid = UUID(str(user_id))

        results = await search_documents(
            database_url=database_url,
            user_id=user_uuid,
            query=query,
            top_k=5,
        )

    except Exception:
        return "Document search failed while searching the uploaded documents."

    if not results:
        return "No relevant information was found in the user's uploaded documents."

    formatted_results = []

    for result in results:
        formatted_results.append(
            (
                f"Source: {result['filename']}\n"
                f"Chunk: {result['chunk_index']}\n"
                f"Similarity: {result['similarity']:.4f}\n"
                f"Content:\n{result['content']}"
            )
        )

    return "\n\n---\n\n".join(formatted_results)