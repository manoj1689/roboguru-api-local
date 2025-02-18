from pydantic import BaseModel
from typing import Optional, List

class EducationLevelBase(BaseModel):
    name: str
    description: Optional[str] = None

class EducationLevelCreate(EducationLevelBase):
    pass

class EducationLevelUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]

class EducationLevelResponse(EducationLevelBase):
    id: str
    classes: List[str] = []

    class Config:
        from_attributes = True
