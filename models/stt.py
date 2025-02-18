from sqlalchemy import Float, DateTime, Integer, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime




class STTModel(Base):
    __tablename__ = "stt"

    id = Column(Integer, primary_key=True, index=True)
    audio_file = Column(Text, nullable=False)  
    language_code = Column(String, default="en") 
    audio_text = Column(Text, nullable=True) 
    audio_time_in_sec = Column(Float, nullable=True) 
    model_used = Column(String, default="whisper-1")  
    timestamp = Column(DateTime, default=datetime.utcnow)  
