import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import DocumentNotFoundError
from app.core.messages import MSG_DOC_NOT_FOUND
from app.schemas.question import AskRequest
from app.services.query_service import QueryService

router = APIRouter(prefix="/ask", tags=["Questions"])


@router.post(
    "",
    summary="Ask a grounded question about a contract (Server-Sent Events streaming)",
    response_class=StreamingResponse,
)
async def ask_question(
    request: AskRequest,
    x_request_id: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    req_id = x_request_id or f"req-{uuid.uuid4()}"
    service = QueryService(session)

    try:
        # Pre-flight check document existence
        doc = await service.doc_repo.get_by_id(request.document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MSG_DOC_NOT_FOUND,
            )

        async def sse_event_generator():
            async for event in service.ask_stream(request=request, request_id=req_id):
                event_type = event["event"]
                data = event["data"]
                yield f"event: {event_type}\ndata: {data}\n\n"

        return StreamingResponse(
            sse_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": req_id,
            },
        )
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_DOC_NOT_FOUND,
        )
