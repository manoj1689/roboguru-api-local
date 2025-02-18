from sqlalchemy import DateTime, Integer, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime


class ChatModel(Base, BaseMixin):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    request_message = Column(Text, nullable=True)
    response_message = Column(Text, nullable=True)
    chat_summary = Column(Text, nullable=True)
    status = Column(Enum("active", "deleted", name="chat_status"), default="active")
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    model_used = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="chats")
    