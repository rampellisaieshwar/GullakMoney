from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("app.errors")

def add_error_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTPException: {exc.status_code} - {exc.detail} on {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error.get("loc", []))
            msg = error.get("msg")
            errors.append(f"{loc}: {msg}")
        logger.warning(f"Validation error on {request.url.path}: {errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Input validation failed",
                "errors": errors
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled system error: {str(exc)} on {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred. Please try again later."}
        )
