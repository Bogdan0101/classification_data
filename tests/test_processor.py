from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest
from app.schemas import LLMClassificationResponse, RowSchema, ChannelEnum
from app.services.processor import ProcessorCSV


@pytest.mark.asyncio
async def test_process_csv_file_success(mock_llm_response):
    schema = [
        RowSchema(
            id="REQ-001",
            channel=ChannelEnum.EMAIL,
            timestamp=datetime.now(),
            raw_text="Не працює пошта",
        ),
    ]

    mock_llm_obj = LLMClassificationResponse(**mock_llm_response)

    with patch(
            "app.services.processor.request_gemini_async",
            new_callable=AsyncMock,
            return_value=mock_llm_obj,
    ):
        processor = ProcessorCSV()
        results = await processor.run_process_csv(schema)

    assert len(results) == 1
    assert results[0].category == "bug/support"
    assert results[0].target_department == "other"
