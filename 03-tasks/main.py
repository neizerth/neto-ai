from fastapi import FastAPI

from api.router import api_router

app = FastAPI(
    title="Task Management API",
    description="Минимальный REST API для управления задачами",
    version="1.0.0",
)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
