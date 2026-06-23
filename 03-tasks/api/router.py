from fastapi import APIRouter

from api.endpoints import tasks

api_router = APIRouter()
api_router.include_router(tasks.router)
