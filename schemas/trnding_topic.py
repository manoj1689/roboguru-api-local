from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class UpdateTrendingTopicRequest(BaseModel):
    topic_id: str
    is_trending: bool
    priority: int = 0
