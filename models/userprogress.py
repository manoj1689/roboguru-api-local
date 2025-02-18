from sqlalchemy import DateTime, Boolean, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime



class UserTopicProgress(Base, BaseMixin):
    __tablename__ = "user_topic_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    topic_id = Column(String, ForeignKey("topics.id"))
    is_completed = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")
