from fastapi import FastAPI

from api.exception_handlers import app_error_handler
from api.feedback import router as feedback_router
from api.healthcheck import router as health_router
from api.profile import router as profile_router
from api.recommendations import history_router, router as recommendations_router
from config.database import init_db
from services.exceptions import AppError

app = FastAPI(
    title="Leisure Recommendation API",
    description="Персональные рекомендации досуга на базе LLM",
    version="1.0.0",
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(recommendations_router)
app.include_router(history_router)
app.include_router(profile_router)
app.include_router(feedback_router)
app.include_router(health_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
