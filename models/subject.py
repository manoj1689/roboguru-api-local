from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from models.base import BaseMixin

class Subject(BaseMixin, Base):
    __tablename__ = "subjects"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    class_id = Column(String, ForeignKey("classes.id"))
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    image_prompt = Column(String, nullable=True)
    class_ = relationship("Class", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject")
