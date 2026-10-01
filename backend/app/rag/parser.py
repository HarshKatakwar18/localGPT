from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
}


def extract_text(
    filename: str,
    content: bytes,
) -> str:

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if extension == ".txt":
        return content.decode(
            "utf-8",
            errors="replace",
        )

    if extension == ".pdf":
        return _extract_pdf_text(content)

    if extension == ".docx":
        return _extract_docx_text(content)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


def _extract_pdf_text(
    content: bytes,
) -> str:

    reader = PdfReader(
        BytesIO(content)
    )

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def _extract_docx_text(
    content: bytes,
) -> str:

    document = Document(
        BytesIO(content)
    )

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)