from pydantic import BaseModel
from typing import List

class UpdateProgressRequest(BaseModel):
    topic_id: str
    is_completed: bool

class UserProgressResponse(BaseModel):
    user_id: str
    subjects: List[str]

    class Config:
        orm_mode = True
