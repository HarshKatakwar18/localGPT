import asyncio
import os
import tempfile
from pathlib import Path

from fastapi.responses import Response

from app.voice.tts import generate_speech

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_current_user

from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)


TRANSCRIBE_MODEL = "gemini-3.5-transcribe"

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10 MB


ALLOWED_AUDIO_TYPES = {
    "audio/webm": ".webm",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".mp4",
    "audio/ogg": ".ogg",
    "audio/aac": ".aac",
    "audio/flac": ".flac",
}


def _transcribe_audio(file_path: str, mime_type: str) -> str:
    """
    Run Gemini transcription synchronously.

    This function is executed in a worker thread so that the
    FastAPI event loop is not blocked.
    """

    from google import genai

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not configured in the backend .env file."
        )

    client = genai.Client(api_key=api_key)

    audio_file = client.files.upload(
        file=file_path,
        config={
            "mime_type": mime_type,
        },
    )

    interaction = client.interactions.create(
        model=TRANSCRIBE_MODEL,
        input=[
            {
                "type": "audio",
                "uri": audio_file.uri,
                "mime_type": audio_file.mime_type,
            }
        ],
        generation_config={
            "transcription_config": {
                "mode": "smart",
                "language_codes": [],
            }
        },
    )

    return (interaction.output_text or "").strip()


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """
    Transcribe a short user voice recording using Gemini 3.5 Transcribe.
    """

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="Audio content type is missing.",
        )

    base_content_type = file.content_type.split(";")[0].lower()

    if base_content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Please use WebM, WAV, MP3, MP4, OGG, AAC, or FLAC."
            ),
        )

    extension = ALLOWED_AUDIO_TYPES[base_content_type]

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_path = temp_file.name

            total_size = 0

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_AUDIO_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio recording is too large. Maximum size is 10 MB.",
                    )

                temp_file.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The audio recording is empty.",
            )

        transcript = await asyncio.to_thread(
            _transcribe_audio,
            temp_path,
            base_content_type,
        )

        if not transcript:
            return {
                "text": "",
                "message": "No speech was detected.",
            }

        return {
            "text": transcript,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(f"Speech transcription failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Speech transcription failed. Please try again.",
        ) from exc

    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass

        await file.close()
        
        
class SpeakRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


@router.post("/speak")
async def speak(
    request: SpeakRequest,
    current_user=Depends(get_current_user),
):
    """
    Generate speech from assistant text using Gemini TTS.
    """

    try:
        audio_data = await generate_speech(request.text)

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-store",
            },
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print(f"TTS generation failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Unable to generate speech.",
        ) from exc        