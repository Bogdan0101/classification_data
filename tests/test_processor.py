from unittest.mock import AsyncMock, patch
import pandas as pd
import pytest
from app.schemas import LLMClassificationResponse
from app.services.processor import process_csv


@pytest.mark.asyncio
async def test_process_csv_file_success(mock_llm_response):
    df = pd.DataFrame(
        [
            {
                "id": "1",
                "channel": "email",
                "request_text": "Не працює пошта",
            }
        ]
    )

    mock_llm_obj = LLMClassificationResponse(**mock_llm_response)

    with patch(
        "app.services.processor.request_gemini_async",
        new_callable=AsyncMock,
        return_value=mock_llm_obj,
    ):
        results = await process_csv(df.to_dict(orient="records"))

    assert len(results) == 1
    assert results[0]["category"] == "bug/support"
    assert results[0]["target_department"] == "other"
