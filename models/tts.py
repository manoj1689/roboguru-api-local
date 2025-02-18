from sqlalchemy import DateTime, Integer, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime


class TTSModel(Base):
    __tablename__ = "tts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False) 
    language_code = Column(String, default="en") 
    audio_file = Column(Text, nullable=True)  
    characters_used = Column(Integer, nullable=True) 
    model_used = Column(String, default="gpt-4o-audio-preview")
    timestamp = Column(DateTime, default=datetime.utcnow)
