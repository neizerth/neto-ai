from llm.base_provider import BaseLLMProvider
from llm.schemas import (
    AlternativeOption,
    ClarificationPayload,
    FollowupQuestion,
    RecommendationPayload,
)


class FakeLLMProvider(BaseLLMProvider):
    """Детерминированный провайдер для тестов (OPENAI_API_KEY=test-key)."""

    DEFAULT_QUESTIONS = [
        FollowupQuestion(
            id="budget",
            text="Какой у вас примерный бюджет на день?",
            hint="Например: до 3000 ₽ или бесплатно",
        ),
        FollowupQuestion(
            id="company",
            text="Планируете провести время один или с компанией?",
            hint=None,
        ),
    ]

    def _needs_clarification(self, user_query: str) -> bool:
        q = user_query.lower()
        if "не знаю" in q:
            return True
        detail_keywords = ["бюджет", "один", "одному", "дома", "минимальн", "без затрат"]
        if sum(1 for k in detail_keywords if k in q) >= 2:
            return False
        if len(user_query) > 100:
            return False
        return len(user_query) < 80

    async def generate_clarification(
        self, user_query: str, profile: dict | None
    ) -> ClarificationPayload:
        if self._needs_clarification(user_query):
            return ClarificationPayload(
                needs_clarification=True,
                questions=self.DEFAULT_QUESTIONS,
                extracted_context={},
            )
        return ClarificationPayload(
            needs_clarification=False,
            questions=[],
            extracted_context={"source": "from_query"},
        )

    async def generate_recommendation(
        self, user_query: str, context: dict[str, str], profile: dict | None
    ) -> RecommendationPayload:
        return RecommendationPayload(
            main_recommendation=(
                "Прогулка по парку Горького с остановкой в кафе на набережной."
            ),
            alternatives=[
                AlternativeOption(
                    title="Поход в музей",
                    description="Посетите экспозицию современного искусства с другом.",
                    budget_estimation="1000–3000 ₽",
                    time_estimation="3–4 часа",
                )
            ],
            reasoning="Учитывая умеренный бюджет и компанию друга, подойдёт активная прогулка.",
            budget_estimation="2000–5000 ₽",
            time_estimation="4–6 часов",
        )
