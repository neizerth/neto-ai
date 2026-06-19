"""
Общие фикстуры для TDD-тестов сервиса рекомендаций досуга.

На этапе RED фикстуры готовы к использованию после реализации логики.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from config.database import init_db, reset_db


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    reset_db()
    yield


from main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Эталонные данные (контракт из docs/models.md)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_query() -> str:
    return "Не знаю, как провести субботу в Москве"


@pytest.fixture
def sample_profile_payload() -> dict[str, Any]:
    return {
        "budget": "medium",
        "activity_level": "moderate",
        "favorite_activities": ["кино", "прогулки"],
        "disliked_activities": ["клубы"],
    }


@pytest.fixture
def sample_clarification_payload() -> dict[str, Any]:
    return {
        "needs_clarification": True,
        "questions": [
            {
                "id": "budget",
                "text": "Какой у вас примерный бюджет на день?",
                "hint": "Например: до 3000 ₽ или бесплатно",
            },
            {
                "id": "company",
                "text": "Планируете провести время один или с компанией?",
                "hint": None,
            },
        ],
        "extracted_context": {},
    }


@pytest.fixture
def sample_recommendation_payload() -> dict[str, Any]:
    return {
        "main_recommendation": (
            "Прогулка по парку Горького с остановкой в кафе на набережной."
        ),
        "alternatives": [
            {
                "title": "Поход в музей",
                "description": "Посетите экспозицию современного искусства с другом.",
                "budget_estimation": "1000–3000 ₽",
                "time_estimation": "3–4 часа",
            }
        ],
        "reasoning": "Учитывая умеренный бюджет и компанию друга, подойдёт активная прогулка.",
        "budget_estimation": "2000–5000 ₽",
        "time_estimation": "4–6 часов",
    }


@pytest.fixture
def sample_continue_answers() -> list[dict[str, str]]:
    return [
        {"question_id": "budget", "answer": "До 5000 ₽"},
        {"question_id": "company", "answer": "С другом"},
    ]


@pytest.fixture
def sample_feedback_payload() -> dict[str, Any]:
    return {
        "recommendation_id": 1,
        "rating": 5,
        "comment": "Отличная идея!",
    }


@pytest.fixture
def fixed_datetime() -> datetime:
    return datetime(2026, 6, 19, 14, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_llm_provider(sample_clarification_payload, sample_recommendation_payload):
    """Мок LLM-провайдера — для integration-тестов сервисов."""
    provider = AsyncMock()
    provider.generate_clarification.return_value = sample_clarification_payload
    provider.generate_recommendation.return_value = sample_recommendation_payload
    return provider


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
