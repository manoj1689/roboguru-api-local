from pydantic import BaseModel
from typing import Optional

class ClassBase(BaseModel):
    name: str
    tagline: str 
    image_link: str

class ClassCreate(ClassBase):
    level_id: str

class ClassUpdate(BaseModel):
    level_id: Optional[str]
    name: Optional[str]
    tagline: Optional[str]
    image_link: Optional[str]

class Class(ClassBase):
    id: str

    class Config:
        from_attributes = True  
