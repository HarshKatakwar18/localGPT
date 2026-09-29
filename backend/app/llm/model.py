import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


def get_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured in the backend .env file."
        )

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=0.2,
        google_api_key=api_key,
        max_retries=0,
    )