from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.deps import DbSession
from app.models.document import Document, DocumentType
from app.schemas.document import DocumentResponse

router = APIRouter()

UPLOAD_DIR = Path("storage/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    db: DbSession,
    file: Annotated[UploadFile, File()],
    document_type: Annotated[DocumentType, Form()] = DocumentType.GENERAL,
) -> Document:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Supported types are PDF, DOCX, and TXT.",
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)

    storage_filename = f"{uuid4()}_{file.filename}"
    storage_path = UPLOAD_DIR / storage_filename

    storage_path.write_bytes(file_bytes)

    document = Document(
        original_filename=file.filename or "unknown",
        storage_path=str(storage_path),
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        document_type=document_type,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: DbSession,
) -> list[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()
