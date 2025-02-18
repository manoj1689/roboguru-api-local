from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin



class Chapter(Base, BaseMixin):
    __tablename__ = "chapters"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    subject = relationship("Subject", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter")
