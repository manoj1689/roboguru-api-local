from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from .chat import ChatResponse

class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    started_at: datetime

class SessionResponse(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    chats: List[ChatResponse] = []

    class Config:
        from_attributes = True
