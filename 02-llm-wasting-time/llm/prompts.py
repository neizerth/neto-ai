SYSTEM_PROMPT = (
    "Ты — помощник по планированию досуга. Отвечай только валидным JSON "
    "на русском языке, без markdown и пояснений вне JSON."
)

CLARIFICATION_PROMPT = (
    "Проанализируй запрос пользователя о досуге. Если данных недостаточно "
    "для персональной рекомендации — верни needs_clarification=true и до 5 "
    "уточняющих вопросов. Иначе needs_clarification=false и extracted_context "
    "с уже известными фактами."
)

RECOMMENDATION_PROMPT = (
    "На основе запроса и собранного контекста сформируй персональную "
    "рекомендацию досуга: main_recommendation, alternatives (до 5), reasoning, "
    "budget_estimation, time_estimation."
)


def _format_profile(profile: dict | None) -> str:
    if not profile:
        return "Профиль не указан."
    lines = []
    if profile.get("budget"):
        lines.append(f"Бюджет: {profile['budget']}")
    if profile.get("activity_level"):
        lines.append(f"Активность: {profile['activity_level']}")
    if profile.get("favorite_activities"):
        lines.append(f"Нравится: {', '.join(profile['favorite_activities'])}")
    if profile.get("disliked_activities"):
        lines.append(f"Не нравится: {', '.join(profile['disliked_activities'])}")
    return "\n".join(lines) if lines else "Профиль пуст."


def build_clarification_user_prompt(user_query: str, profile: dict | None) -> str:
    return (
        f"Запрос пользователя:\n{user_query}\n\n"
        f"Профиль:\n{_format_profile(profile)}"
    )


def build_recommendation_user_prompt(
    user_query: str, context: dict[str, str], profile: dict | None
) -> str:
    context_lines = "\n".join(f"- {k}: {v}" for k, v in context.items()) or "Нет"
    return (
        f"Запрос пользователя:\n{user_query}\n\n"
        f"Собранный контекст:\n{context_lines}\n\n"
        f"Профиль:\n{_format_profile(profile)}"
    )
