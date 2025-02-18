from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class QuestionInput(BaseModel):
    session_id: str
    class_name: str
    subject_name: str
    chapter_name: str
    topic_name: str
    question: str
    chat_summary: Optional[str] = None 

class ChatBase(BaseModel):
    session_id: uuid.UUID
    request_message: str
    response_message: str

class ChatStructuredResponse(BaseModel):
    answer: str
    suggested_questions: Optional[List[str]] = None
    chat_summary: Optional[str] = None 
    
class ChatResponse(ChatBase):
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

