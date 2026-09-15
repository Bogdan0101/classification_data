import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def mock_llm_response():
    return {
        "id": "1",
        "channel": "email",
        "short_summary": "Тестова проблема",
        "category": "bug/support",
        "target_department": "other",
        "priority": "high",
        "needs_clarification": False,
        "clarification_reason": None,
    }


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
