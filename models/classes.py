from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from models.base import BaseMixin


class Class(BaseMixin, Base):
    __tablename__ = "classes"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    level_id = Column(String, ForeignKey("education_levels.id"))
    education_level = relationship("EducationLevel", back_populates="classes")
    subjects = relationship("Subject", back_populates="class_")
    users = relationship("User", back_populates="user_class_details")
    topics = relationship("Topic", back_populates="class_")
