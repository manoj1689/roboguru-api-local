from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, Enum, Text, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSON

class BaseMixin:
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class EducationLevel(Base, BaseMixin):
    __tablename__ = "education_levels"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    classes = relationship("Class", back_populates="education_level")
    users = relationship("User", back_populates="education")

class Class(Base, BaseMixin):
    __tablename__ = "classes"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    level_id = Column(String, ForeignKey("education_levels.id"))
    education_level = relationship("EducationLevel", back_populates="classes")
    subjects = relationship("Subject", back_populates="class_")
    users = relationship("User", back_populates="user_class_details")
    topics = relationship("Topic", back_populates="class_")

class Subject(Base, BaseMixin):
    __tablename__ = "subjects"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    class_id = Column(String, ForeignKey("classes.id"))
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    image_prompt = Column(String, nullable=True)
    class_ = relationship("Class", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject")

class Chapter(Base, BaseMixin):
    __tablename__ = "chapters"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    tagline = Column(String, nullable=True)
    image_link = Column(String, nullable=True)
    subject = relationship("Subject", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter")

class Topic(Base, BaseMixin):
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

class User(Base, BaseMixin):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True,default=lambda: str(uuid.uuid4()), index=True)
    device_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    mobile_number = Column(String, unique=True, index=True, nullable=True)
    otp = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    email = Column(String, nullable=True)
    user_identifier = Column(String, unique=True, index=True, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    occupation = Column(String, nullable=True)
    education_level = Column(String, ForeignKey("education_levels.id"))  
    user_class = Column(String, ForeignKey("classes.id")) 
    language = Column(String, nullable=True)  
    profile_image = Column(String, nullable=True) 
    

    type = Column(Enum("superadmin", "admin", "staff", "normal", name="user_type"), default="normal")

    is_superadmin = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    is_normal = Column(Boolean, default=True)

    progress = relationship("UserTopicProgress", back_populates="user")
    education = relationship("EducationLevel", back_populates="users")
    user_class_details = relationship("Class", back_populates="users")

class SessionModel(Base, BaseMixin):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(Enum("active", "completed", "deleted", name="session_status"), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    title = Column(String, nullable=True)  
    last_message = Column(String, nullable=True)  
    last_message_time = Column(DateTime, nullable=True)  

    chats = relationship("ChatModel", back_populates="session")


class ChatModel(Base, BaseMixin):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    request_message = Column(Text, nullable=True)
    response_message = Column(Text, nullable=True)
    status = Column(Enum("active", "deleted", name="chat_status"), default="active")
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    model_used = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionModel", back_populates="chats")
    
class STTModel(Base):
    __tablename__ = "stt"

    id = Column(Integer, primary_key=True, index=True)
    audio_file = Column(Text, nullable=False)  
    language_code = Column(String, default="en") 
    audio_text = Column(Text, nullable=True) 
    audio_time_in_sec = Column(Float, nullable=True) 
    model_used = Column(String, default="whisper-1")  
    timestamp = Column(DateTime, default=datetime.utcnow)  


class TTSModel(Base):
    __tablename__ = "tts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False) 
    language_code = Column(String, default="en") 
    audio_file = Column(Text, nullable=True)  
    characters_used = Column(Integer, nullable=True) 
    model_used = Column(String, default="gpt-4o-audio-preview")
    timestamp = Column(DateTime, default=datetime.utcnow)

class ImageModel(Base):
    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ImagesToTextModel(Base):
    __tablename__ = "images_to_text"

    id = Column(Integer, primary_key=True, index=True)
    text_response = Column(Text, nullable=False)
    model_used = Column(String, default="vision-model-1")
    token_used = Column(Integer, default=0)
    language_used = Column(String, default="en")
    timestamp = Column(DateTime, default=datetime.utcnow)

# === UserTopicProgress Model ===
class UserTopicProgress(Base, BaseMixin):
    __tablename__ = "user_topic_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    topic_id = Column(String, ForeignKey("topics.id"))
    is_completed = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")