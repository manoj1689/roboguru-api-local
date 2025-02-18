from pydantic import BaseModel, root_validator, Field, EmailStr
from typing import Optional
from datetime import date, datetime

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


class OTPRequest(BaseModel):
    mobile_number: str

class OTPVerification(BaseModel):
    mobile_number: str
    otp: str

class AdminLogin(BaseModel):
    mobile_number: str
    otp: str
