import time
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.llm_service import LLMOutputError, generate_estimation
from app.services.providers import LLMProvider, ProviderError, get_provider

router = APIRouter(tags=["estimations"])


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(
    request: EstimationRequest,
    provider: Annotated[LLMProvider, Depends(get_provider)],
) -> EstimationResponse:
    created_at = datetime.now(UTC)
    started = time.perf_counter()
    try:
        result = await generate_estimation(request.transcription, provider=provider)
    except (LLMOutputError, ProviderError) as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    latency_ms = round((time.perf_counter() - started) * 1000)
    return EstimationResponse.from_result(result, latency_ms=latency_ms, created_at=created_at)
