from sqlalchemy import DECIMAL, Integer, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from .base import BaseMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSON


class Exam(Base, BaseMixin):
    __tablename__ = "exams_and_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)  

    class_name = Column(String, nullable=False)
    subject_name = Column(String,  nullable=False)
    chapter_name = Column(String, nullable=True)
    topic_name = Column(String, nullable=True)

    exam_title = Column(String(255), nullable=True)
    exam_description = Column(Text, nullable=True)

    questions_with_answers = Column(JSON, nullable=True) 
    answers = Column(JSON, nullable=True)  
    score = Column(DECIMAL(5, 2), nullable=True)  

    status = Column(Enum(
        'draft', 'ongoing', 'time_over', 'answer_submission_started', 
        'evaluating_result', 'completed', name='exam_status'
    ), default='draft', nullable=False)

    remark = Column(Text, nullable=True)
    user = relationship("User", back_populates="exams")
