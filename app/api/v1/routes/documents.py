import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MAX_PDF_SIZE_MB
from app.core.database import get_db
from app.core.exceptions import DocumentNotFoundError
from app.core.messages import (
    MSG_DOC_ALREADY_EXISTS,
    MSG_DOC_NOT_FOUND,
    MSG_DOC_QUEUED,
    MSG_FILE_TOO_LARGE,
    MSG_INVALID_FILE_TYPE,
)
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentStatusResponse, DocumentUploadResponse
from app.services.ingest_service import IngestService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload contract PDF for ingestion",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF contract file to ingest"),
    session: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MSG_INVALID_FILE_TYPE,
        )

    file_bytes = await file.read()
    max_bytes = MAX_PDF_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=MSG_FILE_TOO_LARGE.format(max_mb=MAX_PDF_SIZE_MB),
        )

    service = IngestService(session)
    document, already_exists, job_id = await service.ingest(
        file_bytes=file_bytes, filename=file.filename
    )

    if already_exists:
        return DocumentUploadResponse(
            document_id=document.id,
            job_id=None,
            status="ALREADY_EXISTS",
            message=MSG_DOC_ALREADY_EXISTS,
        )

    return DocumentUploadResponse(
        document_id=document.id,
        job_id=job_id,
        status="PENDING",
        message=MSG_DOC_QUEUED,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentStatusResponse,
    summary="Get document ingestion status and metadata",
)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    repo = DocumentRepository(session)
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_DOC_NOT_FOUND,
        )

    return DocumentStatusResponse.model_validate(document)
