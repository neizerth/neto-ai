from fastapi import Request
from fastapi.responses import JSONResponse

from services.exceptions import AppError


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"detail": str(exc), "error_code": exc.error_code},
    )
