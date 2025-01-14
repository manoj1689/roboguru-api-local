from pydantic import BaseModel, Field, root_validator, EmailStr
from typing import Optional, Dict, List
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
    title: str
    status: str
    last_message: Optional[str] = None 
    last_message_time: Optional[datetime] = None
    started_at: datetime
    ended_at: Optional[datetime] = None 

class SessionListResponse(BaseModel):
    success: bool
    message: str
    data: List[SessionOneResponse]  # Change to use SessionOneResponse here



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

class UpdateTrendingTopicRequest(BaseModel):
    topic_id: str
    is_trending: bool
    priority: int = 0


class TokenRequest(BaseModel):
    refresh_token: str

class FirebaseLoginInput(BaseModel):
    id_token: str

# class NotificationRequest(BaseModel):
#     uid: str  # UID of the user
#     operation: str  # Operation type (e.g., SUSPENDUSER, UPDATE_CARD_METADATA)


class NotificationRequest(BaseModel):
    uid: str  # UID of the user
    topic: str  # Topic for grouping notifications
    title: str  # Notification title
    body: str  # Notification body
