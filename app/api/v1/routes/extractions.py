import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ClauseType
from app.core.database import get_db
from app.core.exceptions import DocumentNotFoundError, ExtractionValidationError
from app.core.messages import MSG_DOC_NOT_FOUND, MSG_EXTRACTION_FAILED, MSG_EXTRACTION_NOT_FOUND
from app.repositories.extraction_repository import ExtractionRepository
from app.schemas.extraction import (
    ClauseResultDetailSchema,
    ExtractionRequest,
    ExtractionResponse,
)
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/extract", tags=["Extractions"])


@router.post(
    "",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured clauses from contract",
)
async def extract_clauses(
    request: ExtractionRequest,
    x_request_id: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> ExtractionResponse:
    req_id = x_request_id or f"req-{uuid.uuid4()}"
    service = ExtractionService(session)

    try:
        return await service.extract(request=request, request_id=req_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_DOC_NOT_FOUND,
        )
    except ExtractionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{MSG_EXTRACTION_FAILED} ({exc})",
        )


@router.get(
    "/{extraction_id}",
    response_model=ExtractionResponse,
    summary="Get extraction result by ID",
)
async def get_extraction(
    extraction_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ExtractionResponse:
    repo = ExtractionRepository(session)
    extraction = await repo.get_with_clauses(extraction_id)
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_EXTRACTION_NOT_FOUND,
        )

    clause_details = [
        ClauseResultDetailSchema(
            id=cr.id,
            clause_type=ClauseType(cr.clause_type),
            is_present=cr.is_present,
            verbatim_quote=cr.verbatim_quote,
            summary=cr.summary,
            page_number=cr.page_number,
            confidence=float(cr.confidence) if cr.confidence is not None else 1.0,
            citation_verified=cr.citation_verified,
            source_chunk_id=cr.source_chunk_id,
            repair_attempts=cr.repair_attempts,
            used_fallback=cr.used_fallback,
        )
        for cr in extraction.clause_results
    ]

    return ExtractionResponse(
        extraction_id=extraction.id,
        document_id=extraction.document_id,
        status=extraction.status,  # type: ignore[arg-type]
        model_id=extraction.model_id,
        prompt_version=extraction.prompt_version,
        clause_results=clause_details,
        cost_usd=float(extraction.total_cost_usd or 0.0),
        input_tokens=extraction.total_input_tokens or 0,
        output_tokens=extraction.total_output_tokens or 0,
        latency_ms=float(extraction.latency_ms or 0.0),
        cache_hit=False,
    )
