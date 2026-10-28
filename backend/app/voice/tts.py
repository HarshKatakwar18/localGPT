import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


TTS_MODEL = "gemini-3.8-flash-lite-tts"
TTS_VOICE = "Kore"


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured in the backend .env file."
        )

    return genai.Client(api_key=api_key)


def clean_text_for_speech(text: str) -> str:
    """
    Convert Markdown-heavy assistant responses into natural speech text.
    """

    text = text.strip()

    if not text:
        return ""

    # Remove fenced code markers
    text = text.replace("```", "")

    # Remove inline code markers
    text = text.replace("`", "")

    lines = []

    for line in text.splitlines():
        line = line.strip()

        # Remove Markdown headings
        while line.startswith("#"):
            line = line[1:].lstrip()

        # Remove bullet markers
        if line.startswith("- "):
            line = line[2:]

        # Remove numbered list markers
        if len(line) > 2 and line[0].isdigit() and line[1:3] == ". ":
            line = line[3:]

        lines.append(line)

    text = "\n".join(lines)

    # Remove common Markdown emphasis
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")
    text = text.replace("_", "")

    cleaned_lines = []

    for line in text.splitlines():

        # Skip Markdown table separator
        if line.strip().startswith("|---"):
            continue

        # Convert table columns into natural pauses
        line = line.replace("|", ", ")

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    return text.strip()


async def generate_speech(text: str) -> bytes:
    """
    Generate WAV audio from text using Gemini TTS.
    """

    cleaned_text = clean_text_for_speech(text)

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    # Keep the first implementation bounded.
    cleaned_text = cleaned_text[:6000]

    client = get_gemini_client()

    response = await client.aio.models.generate_content(
        model=TTS_MODEL,
        contents=cleaned_text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=TTS_VOICE,
                    )
                )
            ),
        ),
    )

    for part in response.parts:
        if part.inline_data:
            return part.inline_data.data

    raise RuntimeError(
        "Gemini TTS did not return audio data."
    )