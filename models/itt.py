from sqlalchemy import DateTime, Integer, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime


class ImageModel(Base):
    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ImagesToTextModel(Base):
    __tablename__ = "images_to_text"

    id = Column(Integer, primary_key=True, index=True)
    text_response = Column(Text, nullable=False)
    model_used = Column(String, default="vision-model-1")
    token_used = Column(Integer, default=0)
    language_used = Column(String, default="en")
    timestamp = Column(DateTime, default=datetime.utcnow)
