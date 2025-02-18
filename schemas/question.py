from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class QuestionRequest(BaseModel):
    class_name: str
    subject_name: str
    chapter_name: Optional[str] = None  
    topic_name: Optional[str] = None 
    num_questions: int = 5
    difficulty: str = "medium"

class MixedQuestionRequest(QuestionRequest):
    question_distribution: Dict[str, int]

class AnswerRequest(BaseModel):
    exam_id: str
    exam_title: str
    class_name: str
    subject_name: str
    chapter_name: str
    topic_name: str
    max_marks: Optional[int] = None 
    questions: List[Dict[str, Any]]