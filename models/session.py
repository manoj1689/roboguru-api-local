from sqlalchemy import DateTime, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime


class SessionModel(Base, BaseMixin):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(Enum("active", "completed", "deleted", name="session_status"), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    title = Column(String, nullable=True)  
    last_message = Column(String, nullable=True)  
    last_message_time = Column(DateTime, nullable=True)  
    chat_summary = Column(Text, nullable=True) 

    chats = relationship("ChatModel", back_populates="session")
