"""
E2E-тесты: полный пользовательский сценарий через HTTP.

Спецификация: docs/README.md (MVP-сценарий), docs/api.md

Запуск: pytest tests/e2e/ -m e2e

Требует реализованных сервисов, API-эндпоинтов и SQLite.
На этапе TDD (RED) все тесты должны проваливаться.
"""

import pytest

pytestmark = pytest.mark.e2e


class TestFullUserJourney:
    """
    Сквозной сценарий MVP:
    1. Сохранить профиль
    2. Начать рекомендацию → получить уточняющие вопросы
    3. Ответить на вопросы → получить рекомендацию
    4. Оставить feedback
    5. Увидеть запись в истории с has_feedback=true
    """

    @pytest.mark.asyncio
    async def test_clarification_flow_with_feedback_and_history(self, client, sample_profile_payload):
        profile_resp = await client.put("/profile", json=sample_profile_payload)
        assert profile_resp.status_code == 200
        profile_id = profile_resp.json()["id"]

        start_resp = await client.post(
            "/recommendation",
            json={
                "user_query": "Не знаю, как провести субботу в Москве",
                "profile_id": profile_id,
                "use_profile": True,
            },
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        assert start_data["status"] == "needs_clarification"
        assert "questions" in start_data
        assert len(start_data["questions"]) >= 1

        session_id = start_data["session_id"]
        answers = [
            {"question_id": q["id"], "answer": f"Ответ на {q['id']}"}
            for q in start_data["questions"]
        ]

        continue_resp = await client.post(
            "/recommendation/continue",
            json={"session_id": session_id, "answers": answers},
        )
        assert continue_resp.status_code == 200
        rec_data = continue_resp.json()
        assert rec_data["status"] == "completed"
        assert rec_data["main_recommendation"]
        assert rec_data["reasoning"]
        assert rec_data["budget_estimation"]
        assert rec_data["time_estimation"]
        recommendation_id = rec_data["recommendation_id"]

        feedback_resp = await client.post(
            "/feedback",
            json={
                "recommendation_id": recommendation_id,
                "rating": 5,
                "comment": "Отличная рекомендация!",
            },
        )
        assert feedback_resp.status_code == 201

        history_resp = await client.get("/history")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert history["total"] >= 1
        item = next(i for i in history["items"] if i["id"] == recommendation_id)
        assert item["has_feedback"] is True

        detail_resp = await client.get(f"/history/{recommendation_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["feedback"] is not None
        assert detail["feedback"]["rating"] == 5

    @pytest.mark.asyncio
    async def test_direct_recommendation_without_clarification(self, client):
        """Запрос с достаточным контекстом → рекомендация без уточнений."""

        response = await client.post(
            "/recommendation",
            json={
                "user_query": (
                    "Хочу спокойно провести вечер дома после тяжёлой недели, "
                    "бюджет минимальный, буду один"
                ),
                "use_profile": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["recommendation_id"] > 0
        assert len(data["main_recommendation"]) >= 10

    @pytest.mark.asyncio
    async def test_duplicate_feedback_rejected(self, client, sample_profile_payload):
        await client.put("/profile", json=sample_profile_payload)

        rec_resp = await client.post(
            "/recommendation",
            json={
                "user_query": "Идеи для спокойного вечера дома одному без затрат",
                "use_profile": False,
            },
        )
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()

        if rec_data["status"] == "needs_clarification":
            answers = [
                {"question_id": q["id"], "answer": "любой"}
                for q in rec_data["questions"]
            ]
            cont = await client.post(
                "/recommendation/continue",
                json={"session_id": rec_data["session_id"], "answers": answers},
            )
            rec_data = cont.json()

        recommendation_id = rec_data["recommendation_id"]

        first = await client.post(
            "/feedback",
            json={"recommendation_id": recommendation_id, "rating": 4},
        )
        assert first.status_code == 201

        second = await client.post(
            "/feedback",
            json={"recommendation_id": recommendation_id, "rating": 3},
        )
        assert second.status_code == 409
        assert second.json()["error_code"] == "FEEDBACK_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_api_health_before_and_after_requests(self, client):
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
