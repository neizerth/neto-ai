import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from api.schemas import RecommendRequest, UsageProfile  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
def sample_request() -> RecommendRequest:
    return RecommendRequest(
        current_phone="iPhone 12",
        usage_profile=UsageProfile.GAMING,
        max_recommendations=3,
    )


@pytest.fixture
def valid_llm_json() -> str:
    return """{
    "upgrade_needed": true,
    "urgency": "recommended",
    "summary": "iPhone 12 уступает в играх современным флагманам.",
    "current_phone_assessment": "Устройство 2020 года с A14 Bionic.",
    "recommendations": [
      {
        "brand": "Apple",
        "model": "iPhone 16 Pro",
        "full_name": "Apple iPhone 16 Pro",
        "reason": "A18 Pro, 120 Гц, лучшее охлаждение.",
        "estimated_price_range": "110 000–130 000 ₽"
      }
    ]
  }"""


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
