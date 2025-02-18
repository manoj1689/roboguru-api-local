from pydantic import BaseModel
from typing import Optional, List
from .chapter import Chapter

class SubjectBase(BaseModel):
    name: str
    tagline: str 
    image_link: str
    image_prompt: str

class SubjectCreate(SubjectBase):
    class_id: str

class SubjectUpdate(BaseModel):
    name: Optional[str]
    tagline: Optional[str]
    class_id: Optional[str]
    image_link: Optional[str]
    image_prompt:Optional[str]

class Subject(SubjectBase):
    id: str
    chapters: List[Chapter] = []

    class Config:
        from_attributes = True  
