from fastapi.responses import JSONResponse
from typing import Optional


def create_response(success: bool, message: str, data: Optional[dict] = None, status_code: Optional[int] = None):
    response_content = {
        "success": success,
        "message": message,
        "data": data or {}
    }
    return JSONResponse(
        status_code=status_code if status_code is not None else (200 if success else 400),
        content=response_content
    )