import pytest
from app.core.constants import ClauseType
from app.core.exceptions import ExtractionValidationError
from app.llm.client import LLMClient, LLMResponse
from app.pipeline.repair_loop import RepairLoop
from app.schemas.extraction import ClauseResultSchema


class MockFlakyLLMClient(LLMClient):
    def __init__(self, fail_times: int = 1):
        self.call_count = 0
        self.fail_times = fail_times

    async def generate(self, prompt, system=None, max_tokens=4096):
        return LLMResponse(content="ok", input_tokens=10, output_tokens=10, model_id="mock", provider="mock", latency_ms=10.0)

    async def generate_structured(self, prompt, schema, system=None):
        self.call_count += 1
        if self.call_count <= self.fail_times:
            # Simulate invalid data (confidence outside range 0-1)
            raise ValueError("Validation error: confidence must be between 0 and 1")

        valid_instance = ClauseResultSchema(
            clause_type=ClauseType.TERMINATION,
            is_present=True,
            verbatim_quote="Either party may terminate upon 30 days notice.",
            summary="30 days termination without cause.",
            page_number=5,
            confidence=0.95,
        )
        return valid_instance, LLMResponse(
            content="{}", input_tokens=20, output_tokens=20, model_id="mock", provider="mock", latency_ms=15.0
        )

    async def stream(self, prompt, system=None):
        yield "mock"


@pytest.mark.asyncio
async def test_repair_loop_recovers_after_repair():
    mock_llm = MockFlakyLLMClient(fail_times=1)
    repair_loop = RepairLoop(max_repairs=2)

    parsed, response, attempts, used_fallback = await repair_loop.execute(
        llm_client=mock_llm,
        prompt="Extract termination clause",
        schema=ClauseResultSchema,
    )

    assert parsed.is_present is True
    assert parsed.clause_type == ClauseType.TERMINATION
    assert attempts == 1
    assert mock_llm.call_count == 2


@pytest.mark.asyncio
async def test_repair_loop_raises_when_all_fail():
    mock_llm = MockFlakyLLMClient(fail_times=5)
    repair_loop = RepairLoop(max_repairs=2)

    with pytest.raises(ExtractionValidationError):
        await repair_loop.execute(
            llm_client=mock_llm,
            prompt="Extract termination clause",
            schema=ClauseResultSchema,
        )
