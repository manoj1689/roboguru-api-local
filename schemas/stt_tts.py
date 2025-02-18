from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
    audio_file: str  
    characters_used: int
    timestamp: datetime
    language_used: str
    model_used: str
    additional_data: Optional[dict] = None