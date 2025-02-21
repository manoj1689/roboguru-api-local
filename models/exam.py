from sqlalchemy import DECIMAL, Integer, Column, Enum, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from models.base import BaseMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSON


class Exam(BaseMixin, Base):
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
    
    # total_marks = Column(DECIMAL(5, 2), nullable=False)
    # total_time_taken = Column(Integer, nullable=False)
    # accuracy = Column(DECIMAL(5, 2), nullable=True)
    # total_correct_answers = Column(Integer, nullable=False)
    # total_incorrect_answers = Column(Integer, nullable=False)
    # total_unanswered_questions = Column(Integer, nullable=False)
    # questions_feedback = Column(JSON, nullable=True)
    # overall_feedback = Column(Text, nullable=True)

    status = Column(Enum(
        'draft', 'ongoing', 'time_over', 'answer_submission_started', 
        'evaluating_result', 'completed', name='exam_status'
    ), default='draft', nullable=False)

    remark = Column(Text, nullable=True)
    user = relationship("User", back_populates="exams")
