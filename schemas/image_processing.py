from pydantic import BaseModel, Field
from typing import List, Optional

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