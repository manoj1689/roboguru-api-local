from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class QuestionRequest(BaseModel):
    class_name: str
    subject_name: str
    chapter_name: Optional[str] = None  
    topic_name: Optional[str] = None 
    num_questions: int = 5
    difficulty: str = "medium"

class ChapterTopic(BaseModel):
    chapter_name: str
    topics: List[str]

class MixedQuestionRequest(BaseModel):
    class_name: str
    subject_name: str
    chapters: List[ChapterTopic]
    num_questions: int
    difficulty: str = "medium"
    question_distribution: Dict[str, int]

# class AnswerRequest(BaseModel):
#     exam_id: str
#     exam_title: str
#     class_name: str
#     subject_name: str
#     chapter_name: str
#     topic_name: str
#     max_marks: Optional[int] = None 
#     questions: List[Dict[str, Any]]
class CorrectAnswer(BaseModel):
    option_index: Optional[int] = None
    value: Optional[bool] = None
    answers: Optional[List[str]] = None
    criteria: Optional[str] = None
class Question(BaseModel):
    id: str
    type: str
    text: str
    options: Optional[List[str]] = None
    marks: int
    correct_answer: CorrectAnswer
    student_answer: Optional[str] = None
class AnswerRequest(BaseModel):
    exam_id: str
    exam_title: str
    class_name: str
    subject_name: str
    chapters: List[ChapterTopic]
    max_marks: int
    exam_start_time: datetime
    exam_end_time: datetime
    questions: List[Question]