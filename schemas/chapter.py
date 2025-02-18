from pydantic import BaseModel
from typing import Optional, List
from .topic import Topic

class ChapterBase(BaseModel):
    name: str
    tagline: str 
    image_link: str

class ChapterCreate(ChapterBase):
    subject_id: str

class ChapterUpdate(BaseModel):
    name: Optional[str]
    tagline: Optional[str] 
    subject_id: Optional[str] 
    image_link: Optional[str]

class Chapter(ChapterBase):
    id: str
    topics: List[Topic] = []

    class Config:
        from_attributes = True 
