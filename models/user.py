from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Boolean, Enum, Text, Float, DECIMAL
from sqlalchemy.orm import relationship
from database import Base
import uuid
from models.base import BaseMixin


class User(BaseMixin, Base):
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

    exams = relationship("Exam", back_populates="user")  
    progress = relationship("UserTopicProgress", back_populates="user")
    education = relationship("EducationLevel", back_populates="users")
    user_class_details = relationship("Class", back_populates="users")