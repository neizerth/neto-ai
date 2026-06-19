from fastapi import FastAPI

from api.router import api_router

app = FastAPI(
    title="Phone Recommendation API",
    description="Рекомендации по обновлению смартфона на базе LLM",
    version="1.0.0",
)
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
