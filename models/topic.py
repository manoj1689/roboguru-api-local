from sqlalchemy import Column, Integer,JSON,Boolean, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from models.base import BaseMixin


class Topic(BaseMixin, Base):
    __tablename__ = "topics"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    details = Column(String, nullable=True)
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    subtopics = Column(JSON, default=list, nullable=True)
    is_trending = Column(Boolean, default=False)  
    priority = Column(Integer, default=0)  
    is_completed = Column(Boolean, default=False)
    
    progress = relationship("UserTopicProgress", back_populates="topic")
    chapter_id = Column(String, ForeignKey("chapters.id"))
    class_id = Column(String, ForeignKey("classes.id")) 
    chapter = relationship("Chapter", back_populates="topics")
    class_ = relationship("Class", back_populates="topics") 
