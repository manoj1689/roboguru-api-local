from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin

class EducationLevel(Base, BaseMixin):
    __tablename__ = "education_levels"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    classes = relationship("Class", back_populates="education_level")
    users = relationship("User", back_populates="education")
