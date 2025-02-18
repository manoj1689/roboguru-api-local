from pydantic import BaseModel
from typing import Optional, List

class TopicBase(BaseModel):
    name: str
    tagline: str 
    image_link: str
    details: Optional[str] = None
    subtopics: Optional[List] = None 

class TopicCreate(TopicBase):
    chapter_id: str

class TopicUpdate(BaseModel):
    name: Optional[str]
    details: Optional[str]
    chapter_id: Optional[str]
    image_link: Optional[str]
    subtopics: Optional[List] = None 

class Topic(TopicBase):
    id: str

    class Config:
        from_attributes = True  
