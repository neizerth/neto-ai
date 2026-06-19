import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

USAGE_OPTIONS = {
    "Повседневное использование": "everyday",
    "Игры": "gaming",
    "Фотография": "photography",
    "Профессиональная фотография": "pro_photography",
    "Видеосъёмка и монтаж": "video_creation",
    "Деловое использование": "business",
    "Долгая автономность": "battery_life",
    "Компактный размер": "compact",
}

URGENCY_LABELS = {
    "not_needed": ("✅ Обновление не требуется", "success"),
    "optional": ("💡 Обновление опционально", "info"),
    "recommended": ("⚠️ Рекомендуется обновление", "warning"),
    "urgent": ("🔴 Срочно рекомендуется обновление", "error"),
}


def render_recommendation_card(rec: dict) -> None:
    with st.container(border=True):
        st.subheader(rec["full_name"])
        st.write(rec["reason"])
        if rec.get("estimated_price_range"):
            st.caption(f"💰 {rec['estimated_price_range']}")


def main() -> None:
    st.set_page_config(
        page_title="Рекомендации смартфонов",
        page_icon="📱",
        layout="centered",
    )

    st.title("📱 Рекомендации по обновлению смартфона")
    st.caption(
        "Укажите текущую модель и сценарий использования — "
        "сервис подскажет, стоит ли обновляться."
    )

    with st.form("recommend_form"):
        current_phone = st.text_input(
            "Текущий телефон *",
            placeholder="Например: iPhone 12, Samsung Galaxy S21",
        )
        usage_label = st.selectbox(
            "Сценарий использования *",
            options=list(USAGE_OPTIONS.keys()),
        )
        additional = st.text_area(
            "Дополнительные пожелания",
            placeholder="Бюджет, предпочитаемый бренд, размер экрана...",
            height=80,
        )
        max_recs = st.slider("Максимум рекомендаций", min_value=1, max_value=5, value=3)

        submitted = st.form_submit_button("🔍 Получить рекомендацию", type="primary")

    if not submitted:
        return

    if not current_phone or not current_phone.strip():
        st.error("Укажите текущую модель телефона")
        return

    payload = {
        "current_phone": current_phone.strip(),
        "usage_profile": USAGE_OPTIONS[usage_label],
        "additional_requirements": additional.strip() or None,
        "max_recommendations": max_recs,
    }

    with st.spinner("Анализируем ваш телефон..."):
        try:
            response = httpx.post(
                f"{API_BASE_URL}/recommend",
                json=payload,
                timeout=60.0,
            )
        except httpx.ConnectError:
            st.error("Не удалось подключиться к API. Убедитесь, что сервер запущен.")
            return
        except httpx.TimeoutException:
            st.error("Превышено время ожидания ответа. Попробуйте позже.")
            return

    if response.status_code == 422:
        st.error("Проверьте корректность введённых данных.")
        st.json(response.json())
        return

    if response.status_code != 200:
        body = response.json()
        detail = body.get("detail", "Неизвестная ошибка")
        if isinstance(detail, dict):
            detail = detail.get("detail", detail)
        st.error(f"Ошибка сервера: {detail}")
        return

    data = response.json()

    st.divider()
    st.header("Результат")

    label, level = URGENCY_LABELS.get(data["urgency"], ("", "info"))
    if label:
        getattr(st, level)(label)

    st.info(data["summary"])
    st.caption(f"Оценка текущего телефона: {data['current_phone_assessment']}")

    if data["recommendations"]:
        st.subheader("Рекомендуемые модели")
        for rec in data["recommendations"]:
            render_recommendation_card(rec)
    elif not data["upgrade_needed"]:
        st.success("Ваш текущий телефон отлично подходит для выбранного сценария!")


if __name__ == "__main__":
    main()
