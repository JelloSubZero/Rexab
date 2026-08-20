from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    """
    HTTPException that renders as the project's unified error body:

        {"error": {"code": "NOT_ROOM_MEMBER", "message": "..."}}
    """

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
        )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:

    if isinstance(exc.detail, dict) and "code" in exc.detail:
        body = exc.detail
    else:
        body = {"code": "HTTP_ERROR", "message": str(exc.detail)}

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": body},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data.",
                "details": exc.errors(),
            }
        },
    )
