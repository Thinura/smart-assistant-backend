from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.api.deps import DbSession
from app.models.audit_log import AuditEventType
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.document_chunk import DocumentChunk
from app.schemas.document import DocumentDetailResponse, DocumentListResponse
from app.schemas.document_chunk import DocumentChunkResponse
from app.services.audit_log_service import AuditLogService
from app.services.document_chunking_service import DocumentChunkingService
from app.services.document_text_extraction_service import DocumentTextExtractionService
from app.services.embedding_service import EmbeddingService

router = APIRouter()

UPLOAD_DIR = Path("storage/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DOCUMENT_TYPE_QUERY = Query(default=None, alias="document_type")
STATUS_QUERY = Query(default=None, alias="status")
LIMIT_QUERY = Query(default=100, ge=1, le=500)


@router.get("", response_model=list[DocumentListResponse])
def list_documents(
    db: DbSession,
    document_type_filter: DocumentType | None = DOCUMENT_TYPE_QUERY,
    status_filter: DocumentStatus | None = STATUS_QUERY,
    limit: int = LIMIT_QUERY,
) -> list[Document]:
    query = db.query(Document)

    if document_type_filter is not None:
        query = query.filter(Document.document_type == document_type_filter)

    if status_filter is not None:
        query = query.filter(Document.status == status_filter)

    return query.order_by(Document.created_at.desc()).limit(limit).all()


@router.post(
    "/upload",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    db: DbSession,
    file: Annotated[UploadFile, File()],
    document_type: Annotated[DocumentType, Form()] = DocumentType.GENERAL,
) -> Document:
    text_extraction_service = DocumentTextExtractionService()

    if not text_extraction_service.is_supported(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. Supported types are: "
                f"{', '.join(sorted(text_extraction_service.supported_content_types))}"
            ),
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

    try:
        extracted_text = text_extraction_service.extract_text(
            file_path=document.storage_path,
            content_type=document.content_type,
        )

        document.extracted_text = extracted_text
        document.status = DocumentStatus.PROCESSED
        chunking_service = DocumentChunkingService()
        chunks = chunking_service.split_text(extracted_text)

        embedding_service = EmbeddingService()

        for index, chunk in enumerate(chunks):
            embedding = embedding_service.generate_embedding(chunk)

            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                )
            )

    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.extracted_text = None
        db.commit()
        raise RuntimeError(f"Failed to extract document text: {exc}") from exc

    AuditLogService(db).record(
        event_type=AuditEventType.DOCUMENT_UPLOADED,
        entity_type="document",
        entity_id=str(document.id),
        actor="system",
        metadata={
            "original_filename": document.original_filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "document_type": document.document_type.value,
            "status": document.status.value,
        },
    )
    db.commit()
    db.refresh(document)

    return document


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def list_document_chunks(
    document_id: UUID,
    db: DbSession,
) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: DbSession,
) -> None:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    storage_path = document.storage_path

    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id,
    ).delete()

    db.delete(document)
    db.commit()

    if storage_path:
        path = Path(storage_path)
        if path.exists() and path.is_file():
            path.unlink()
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    storage_path = document.storage_path

    db.delete(document)
    db.commit()

    if storage_path:
        path = Path(storage_path)
        if path.exists() and path.is_file():
            path.unlink()


@router.post("/{document_id}/reprocess", response_model=DocumentDetailResponse)
def reprocess_document(
    document_id: UUID,
    db: DbSession,
) -> Document:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    path = Path(document.storage_path)

    if not path.exists() or not path.is_file():
        document.status = DocumentStatus.FAILED
        db.commit()
        db.refresh(document)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file not found",
        )

    text_extraction_service = DocumentTextExtractionService()
    chunking_service = DocumentChunkingService()
    embedding_service = EmbeddingService()

    document.status = DocumentStatus.PROCESSING
    db.flush()

    try:
        extracted_text = text_extraction_service.extract_text(
            file_path=document.storage_path,
            content_type=document.content_type,
        )

        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id,
        ).delete()

        document.extracted_text = extracted_text
        document.status = DocumentStatus.PROCESSED

        chunks = chunking_service.split_text(extracted_text)

        for index, chunk in enumerate(chunks):
            embedding = embedding_service.generate_embedding(chunk)

            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                )
            )

    except Exception as exc:
        document.status = DocumentStatus.FAILED
        db.commit()
        db.refresh(document)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document reprocessing failed: {exc}",
        ) from exc

    db.commit()
    db.refresh(document)

    return document
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    path = Path(document.storage_path)

    if not path.exists() or not path.is_file():
        document.status = DocumentStatus.FAILED
        db.commit()
        db.refresh(document)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file not found",
        )

    document.status = DocumentStatus.PROCESSING
    db.flush()

    try:
        extracted_text = text_extraction_service.extract_text(
            path=document.storage_path,
            content_type=document.content_type,
        )

        document.extracted_text = extracted_text
        document.status = DocumentStatus.PROCESSED
        chunking_service.replace_chunks(document=document, text=extracted_text)

    except Exception as exc:
        document.status = DocumentStatus.FAILED
        db.commit()
        db.refresh(document)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document reprocessing failed: {exc}",
        ) from exc

    db.commit()
    db.refresh(document)

    return document


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: UUID,
    db: DbSession,
) -> Document:
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document
