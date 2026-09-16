import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama


load_dotenv()


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
        base_url=os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        ),
        temperature=0.2,
    )