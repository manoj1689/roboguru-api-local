from pydantic import BaseModel, Field, root_validator, EmailStr
from typing import Optional, Dict, List, Union, Any
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import uuid
from fastapi import UploadFile, File

class TopicBase(BaseModel):
    name: str
    tagline: str 
    image_link: str
    details: Optional[str] = None
    subtopics: Optional[List] = None 

class TopicCreate(TopicBase):
    name: str
    details: Optional[str] = None
    tagline: str 
    chapter_id: str
    image_link: str
    subtopics: Optional[List] = None 

class ReadTopicRequest(BaseModel):
    limit: Optional[int] = 10
    name: Optional[str] = None

class TopicUpdate(BaseModel):
    name: Optional[str]
    details: Optional[str]
    chapter_id: Optional[str]
    image_link: Optional[str]
    subtopics: Optional[List] = None 

class Topic(TopicBase):
    id: str

    class Config:
        from_attributes = True  

class ChapterBase(BaseModel):
    name: str
    tagline: str 
    image_link: str

class ChapterCreate(ChapterBase):
    name: str
    tagline: str 
    image_link: str
    subject_id: str

class ReadChapterRequest(BaseModel):
    limit: Optional[int] = 10
    name: Optional[str] = None

class ChapterUpdate(BaseModel):
    name: Optional[str]
    tagline: Optional[str] 
    subject_id: Optional[str] 
    image_link: Optional[str]


class Chapter(ChapterBase):
    id: str
    topics: list[Topic] = []

    class Config:
        from_attributes = True 

class SubjectBase(BaseModel):
    name: str
    tagline: str 
    image_link: str
    image_prompt: str

class ReadSubjectRequest(BaseModel):
    limit: Optional[int] = 10
    name: Optional[str] = None

class SubjectCreate(SubjectBase):
    name: str
    tagline: str 
    class_id : str 
    image_link: str
    image_prompt: str

class SubjectUpdate(BaseModel):
    name: Optional[str]
    tagline: Optional[str]
    class_id: Optional[str]
    image_link: Optional[str]
    image_prompt:Optional[str]


class SubjectData(SubjectBase):
    id: str
    name: str
    tagline: str 
    class_id : str 
    image_link: str
    image_prompt: str


class Subject(SubjectBase):
    id: str
    chapters: list[Chapter] = []

    class Config:
        from_attributes = True  

class ClassBase(BaseModel):
    name: str
    tagline: str 
    image_link: str

class ClassCreate(ClassBase):
    name: str
    tagline: str 
    level_id: str
    image_link: str

class ReadClassesRequest(BaseModel):
    limit: Optional[int] = 10
    name: Optional[str] = None
    
class ClassUpdate(BaseModel):
    level_id: Optional[str]
    name: Optional[str]
    tagline: Optional[str]
    image_link: Optional[str]

class Class(ClassBase):
    id: str

    class Config:
        from_attributes = True  

class EducationLevelBase(BaseModel):
    name: str
    description: Optional[str] = None

class EducationLevelCreate(EducationLevelBase):
    pass

class EducationLevelUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]

class ReadEducationLevelRequest(BaseModel):
    limit: Optional[int] = 10
    name: Optional[str] = None

class EducationLevel(EducationLevelBase):
    id: str

class EducationLevelResponse(EducationLevelBase):
    id: str
    classes: List[str] = []

    class Config:
        from_attributes = True
        
class ResponseModel(BaseModel):
    message: str
    data: Optional[Dict] = None

class ChatRequest(BaseModel):
    session_id: str
    request_message: str

class ChatTopicBasedRequest(BaseModel):
    subject_name: str
    class_name: str
    chapter_name: str
    topic_name: str
    subtopic_name: Optional[str] = None
    request_message: str

class ChatBase(BaseModel):
    session_id: uuid.UUID
    request_message: str
    response_message: str


class ChatResponse(ChatBase):
    session_id: uuid.UUID
    request_message: str
    response_message: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    pass

class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    started_at: datetime

class SessionResponse(SessionBase):
    id: uuid.UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    chats: List[ChatResponse] = []

    class Config:
        from_attributes = True

class SessionOneResponse(BaseModel):
    id: str
    title: Optional[str] = None  
    status: str
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    
class SessionListResponse(BaseModel):
    success: bool
    message: str
    data: List[SessionOneResponse] 



class UserCreate(BaseModel):
    mobile_number: str = Field(..., pattern=r"^\d{10}$")
    type: str = Field(default="normal")

    class Config:
        orm_mode = True

@root_validator(pre=True)
def validate_date_of_birth(cls, values):
    dob = values.get("date_of_birth")
    if dob:
        try:
            # Parse the date in the desired format
            values["date_of_birth"] = datetime.strptime(dob, "%d-%m-%Y").date()
        except ValueError:
            raise ValueError("date_of_birth must be in DD-MM-YYYY format")
    return values

class UpdateRoleRequest(BaseModel):
    role: str

class OTPRequest(BaseModel):
    mobile_number: str

class OTPVerification(BaseModel):
    mobile_number: str
    otp: str

class AdminLogin(BaseModel):
    mobile_number: str
    otp: str


class CurrentUser(BaseModel):
    user_id: str
    type: str

class UserProfileResponse(BaseModel):
    id: int
    name: Optional[str]
    mobile_number: str
    email: Optional[str]
    date_of_birth: Optional[str]
    occupation: Optional[str]
    is_verified: bool
    education_level: Optional[str]
    user_class: Optional[str]
    language: Optional[str]

class UpdateUserProfileRequest(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    date_of_birth: Optional[date]
    occupation: Optional[str]
    education_level: Optional[str]
    user_class: Optional[str]
    language: Optional[str]
    profile_image: Optional[str]


class UpdateTrendingTopicRequest(BaseModel):
    topic_id: str
    is_trending: bool
    priority: int = 0


class TokenRequest(BaseModel):
    refresh_token: str

class FirebaseLoginInput(BaseModel):
    id_token: str


class NotificationRequest(BaseModel):
    uid: str  
    topic: str 
    title: str  
    body: str  

class QuestionInput(BaseModel):
    session_id: str
    class_name: str
    subject_name: str
    chapter_name: str
    topic_name: str
    question: str
    chat_summary: Optional[str] = None 
    
class ChatStructuredResponse(BaseModel):
    answer: str
    suggested_questions: Optional[List[str]] = None
    chat_summary: Optional[str] = None 

class TopicResponse(BaseModel):
    topic_id: str
    is_completed: bool

    class Config:
        orm_mode = True


class ChapterResponse(BaseModel):
    chapter_id: str
    topics: List[TopicResponse]
    chapter_progress: float

    class Config:
        orm_mode = True


class SubjectResponse(BaseModel):
    subject_id: str
    chapters: List[ChapterResponse]
    subject_progress: float


    class Config:
        orm_mode = True
        
class UserProgressResponse(BaseModel):
    user_id: str
    subjects: List[SubjectResponse]

    class Config:
        orm_mode = True


class UpdateProgressRequest(BaseModel):
    topic_id: str
    is_completed: bool

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


class STTInput(BaseModel):
    audio_file: str = Field(..., description="Base64 encoded audio file")
    language_code: Optional[str] = Field("en", description="Language code of the audio")

class STTOutput(BaseModel):
    audio_text: str
    audio_time_in_sec: float
    model_used: str
    language_code: str
    timestamp: datetime
    additional_data: Optional[dict] = None

class TTSInput(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    language_code: Optional[str] = Field("en", description="Language code for speech synthesis")

class TTSOutput(BaseModel):
    audio_file: str  # Base64 encoded audio
    characters_used: int
    timestamp: datetime
    language_used: str
    model_used: str
    additional_data: Optional[dict] = None

class UploadImageOutput(BaseModel):
    image_urls: List[str]

class ImagesToTextInput(BaseModel):
    image_urls: List[str] = Field(..., description="List of Image URLs")
    prompt: str = Field(..., description="Prompt for image analysis")
    language_code: Optional[str] = Field("en", description="Language code for the response")

class ImagesToTextOutput(BaseModel):
    text_response: str
    model_used: str
    token_used: int
    language_used: str
    additional_data: Optional[dict] = None