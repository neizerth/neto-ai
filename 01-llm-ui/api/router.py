from fastapi import APIRouter

from api.endpoints import recommend

api_router = APIRouter()
api_router.include_router(recommend.router)
