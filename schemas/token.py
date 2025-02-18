from pydantic import BaseModel

class TokenRequest(BaseModel):
    refresh_token: str
