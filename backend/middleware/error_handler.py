"""Registers centralized exception handling so every route returns a consistent error shape."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from utils.exceptions import AppException

logger = logging.getLogger("rk_pms")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # exc.errors() can include a "ctx" dict holding the raw exception object from a
        # failed validator (e.g. ValueError) — that's not JSON-serializable, so strip it
        # and keep the human-readable message instead.
        sanitized_errors = []
        for error in exc.errors():
            clean = {k: v for k, v in error.items() if k != "ctx"}
            sanitized_errors.append(clean)

        return JSONResponse(
            status_code=422,
            content={"success": False, "message": "Validation failed", "data": sanitized_errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error", "data": None},
        )
