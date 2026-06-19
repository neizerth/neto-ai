"""
Unit-тесты доменных исключений.

Спецификация: docs/validation.md
"""

import pytest

from services.exceptions import (
    AppError,
    FeedbackAlreadyExistsError,
    LLMParseError,
    ProfileNotFoundError,
    SessionExpiredError,
    SessionInvalidStateError,
    SessionNotFoundError,
    ValidationBusinessError,
)


class TestDomainExceptions:
    def test_llm_parse_error_code(self):
        err = LLMParseError("Невалидный JSON")
        assert err.error_code == "LLM_PARSE_ERROR"

    def test_llm_parse_error_http_status(self):
        err = LLMParseError("Невалидный JSON")
        assert err.http_status == 502

    def test_session_not_found_error_code(self):
        err = SessionNotFoundError("Сессия не найдена")
        assert err.error_code == "SESSION_NOT_FOUND"
        assert err.http_status == 404

    def test_profile_not_found_error_code(self):
        err = ProfileNotFoundError("Профиль не найден")
        assert err.error_code == "PROFILE_NOT_FOUND"

    def test_session_invalid_state_error_code(self):
        err = SessionInvalidStateError("Сессия не ожидает ответов")
        assert err.error_code == "SESSION_INVALID_STATE"
        assert err.http_status == 409

    def test_feedback_already_exists_error_code(self):
        err = FeedbackAlreadyExistsError("Отзыв уже оставлен")
        assert err.error_code == "FEEDBACK_ALREADY_EXISTS"

    def test_session_expired_http_status(self):
        err = SessionExpiredError("Сессия истекла")
        assert err.http_status == 410

    def test_validation_business_error_http_status(self):
        err = ValidationBusinessError("Неизвестный вопрос")
        assert err.http_status == 422

    def test_exceptions_inherit_from_app_error(self):
        assert issubclass(LLMParseError, AppError)
        assert issubclass(SessionNotFoundError, AppError)
