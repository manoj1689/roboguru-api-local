from fastapi.responses import JSONResponse
from typing import Optional


def create_response(success: bool, message: str, data: dict = None, profile_updated: bool = None, status_code: int = None):
    response_content = {
        "success": success,
        "message": message,
    }
    
    if profile_updated is not None:
        response_content["profile_updated"] = profile_updated
    
    response_content["data"] = data if data is not None else {}

    return JSONResponse(
        status_code=status_code if status_code is not None else (200 if success else 400),
        content=response_content
    )
