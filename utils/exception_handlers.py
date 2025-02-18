
from fastapi.exceptions import HTTPException
from fastapi import Request
from utils.response import create_response

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:  # Unauthorized error
        return create_response(
            success=False,
            message="Not authenticated",
            status_code=401
        )
    return create_response(
        success=False,
        message=exc.detail,
        status_code=exc.status_code
    )
