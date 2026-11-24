from fastapi import Request
from models.common_schemas import APIException
from fastapi.responses import JSONResponse
from loguru import logger

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.response.to_dict()
    )