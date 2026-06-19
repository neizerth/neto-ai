"""Доменные исключения — docs/validation.md."""


class AppError(Exception):
    error_code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        if error_code:
            self.error_code = error_code


class LLMError(AppError):
    error_code = "LLM_UNAVAILABLE"
    http_status = 502


class LLMParseError(LLMError):
    error_code = "LLM_PARSE_ERROR"


class NotFoundError(AppError):
    error_code = "NOT_FOUND"
    http_status = 404


class ProfileNotFoundError(NotFoundError):
    error_code = "PROFILE_NOT_FOUND"


class SessionNotFoundError(NotFoundError):
    error_code = "SESSION_NOT_FOUND"


class RecommendationNotFoundError(NotFoundError):
    error_code = "RECOMMENDATION_NOT_FOUND"


class ConflictError(AppError):
    error_code = "CONFLICT"
    http_status = 409


class SessionInvalidStateError(ConflictError):
    error_code = "SESSION_INVALID_STATE"


class FeedbackAlreadyExistsError(ConflictError):
    error_code = "FEEDBACK_ALREADY_EXISTS"


class SessionExpiredError(AppError):
    error_code = "SESSION_EXPIRED"
    http_status = 410


class ValidationBusinessError(AppError):
    error_code = "VALIDATION_ERROR"
    http_status = 422
