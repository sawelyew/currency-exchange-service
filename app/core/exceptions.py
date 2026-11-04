from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.core.logger import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        logger.warning(f"Ошибка валидации Pydantic: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder({
                "success": False,
                "error": "Ошибка валидации данных",
            }),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Ошибка валидации запроса FastAPI: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder({
                "success": False,
                "message": "Переданы некорректные данные",
            })
        )