from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from app.api.dependencies import get_current_user
from app.rag.service import (
    ingest_document,
    list_documents,
    delete_document,
)


router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
}


def get_extension(
    filename: str,
) -> str:

    if "." not in filename:
        return ""

    return "." + filename.rsplit(
        ".",
        1,
    )[1].lower()


@router.post("/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = get_extension(
        file.filename
    )

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported types: PDF, TXT, DOCX."
            ),
        )

    content = await file.read()

    try:
        result = await ingest_document(
            database_url=request.app.state.database_url,
            user_id=current_user["id"],
            filename=file.filename,
            content_type=file.content_type
            or "application/octet-stream",
            content=content,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Failed to process the document.",
        ) from error


@router.get("/documents")
async def get_documents(
    request: Request,
    current_user=Depends(get_current_user),
):
    return await list_documents(
        database_url=request.app.state.database_url,
        user_id=current_user["id"],
    )


@router.delete(
    "/documents/{document_id}"
)
async def remove_document(
    document_id: UUID,
    request: Request,
    current_user=Depends(get_current_user),
):
    deleted = await delete_document(
        database_url=request.app.state.database_url,
        user_id=current_user["id"],
        document_id=document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "message": "Document deleted successfully.",
        "document_id": str(document_id),
    }