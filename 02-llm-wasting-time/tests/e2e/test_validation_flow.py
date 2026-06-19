"""
E2E-тесты: граничные случаи и бизнес-правила валидации через HTTP.

Спецификация: docs/validation.md
"""

import pytest

pytestmark = pytest.mark.e2e


class TestValidationE2E:
    @pytest.mark.asyncio
    async def test_rejects_empty_user_query(self, client):
        response = await client.post("/recommendation", json={"user_query": "   "})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_continue_with_unknown_question_id(self, client):
        start = await client.post(
            "/recommendation",
            json={"user_query": "Не знаю, как провести субботу в Москве"},
        )
        if start.status_code != 200 or start.json()["status"] != "needs_clarification":
            pytest.skip("Требуется сценарий с уточнениями")

        session_id = start.json()["session_id"]
        response = await client.post(
            "/recommendation/continue",
            json={
                "session_id": session_id,
                "answers": [{"question_id": "nonexistent", "answer": "тест"}],
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_history_pagination(self, client):
        response = await client.get("/history?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["items"]) <= 2

    @pytest.mark.asyncio
    async def test_history_invalid_limit(self, client):
        response = await client.get("/history?limit=200")
        assert response.status_code == 422
