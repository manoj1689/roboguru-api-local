import os
import uuid
import base64
import datetime
from typing import List, Optional
from fastapi import status, APIRouter, Depends, HTTPException, UploadFile, File, Header, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from models import STTModel, ImageModel, ImagesToTextModel, TTSModel, User
from sqlalchemy.orm import Session
from database import get_db
from services.auth import get_current_user 
from services.classes import create_response
from dotenv import load_dotenv
import base64


import openai

load_dotenv()

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
BASE_URL= os.getenv("BASE_URL")

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)



from pydantic import BaseModel, Field

class STTInput(BaseModel):
    audio_file: str = Field(..., description="Base64 encoded audio file")
    language_code: Optional[str] = Field("en", description="Language code of the audio")

class STTOutput(BaseModel):
    audio_text: str
    audio_time_in_sec: float
    model_used: str
    language_code: str
    timestamp: datetime.datetime
    additional_data: Optional[dict] = None

class TTSInput(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    language_code: Optional[str] = Field("en", description="Language code for speech synthesis")

class TTSOutput(BaseModel):
    audio_file: str  # Base64 encoded audio
    characters_used: int
    timestamp: datetime.datetime
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

def decode_base64(encoded_str: str) -> bytes:
    try:
        return base64.b64decode(encoded_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 string.")

def encode_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode('utf-8')

def calculate_audio_duration(audio_bytes: bytes, sample_rate: int = 16000) -> float:
    return len(audio_bytes) / (sample_rate * 2)  # Assuming 16-bit audio

@router.post("/speech-to-text/", response_model=STTOutput)
def speech_to_text_endpoint(
    stt_input: STTInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        # Decode Base64 audio data
        audio_bytes = decode_base64(stt_input.audio_file)
        audio_time_in_sec = calculate_audio_duration(audio_bytes)

        # Create a temporary file path for the audio
        temp_audio_path = f"{UPLOAD_DIR}/temp_{uuid.uuid4()}.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes)

        with open(temp_audio_path, "rb") as audio_file:
            # Make API request to OpenAI
            response = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )

        os.remove(temp_audio_path)

        # Save transcription data to the database
        stt_output = STTModel(
            audio_file=temp_audio_path,  
            language_code=stt_input.language_code,
            audio_text=response.text,
            audio_time_in_sec=audio_time_in_sec,
            model_used="whisper-1",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(stt_output)
        db.commit()
        db.refresh(stt_output)

        return create_response(
            success=True,
            message="Speech-to-text conversion successful",
            data={
                "audio_text": stt_output.audio_text,
                "audio_time_in_sec": stt_output.audio_time_in_sec,
                "model_used": stt_output.model_used,
                "language_code": stt_output.language_code,
                "timestamp": stt_output.timestamp.isoformat(),
            }
        )
    except Exception as e:
        return create_response(
            success=False,
            message=f"Speech-to-text conversion failed: {str(e)}"
        )



# Define the new folder for storing TTS audio files
TTS_UPLOAD_DIR = "uploaded_audio"
os.makedirs(TTS_UPLOAD_DIR, exist_ok=True)

router.mount("/uploaded_audio", StaticFiles(directory=UPLOAD_DIR), name="uploaded_audio")


@router.post("/text-to-speech/", response_model=TTSOutput)
def text_to_speech_endpoint(
    tts_input: TTSInput,
    current_user: str = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    try:
        # Call OpenAI TTS API
        response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=tts_input.text
        )
        # Combine the response into a single byte stream
        audio_content = b''.join(response.iter_bytes())

        # Save the audio content to a file in the new folder
        unique_filename = f"tts_{uuid.uuid4()}.wav"
        temp_audio_path = os.path.join(TTS_UPLOAD_DIR, unique_filename)
        with open(temp_audio_path, "wb") as f:
            f.write(audio_content)

        # Encode audio content to Base64
        audio_base64 = encode_base64(audio_content)

        # Save the file path and other details in the database
        tts_record = TTSModel(
            text=tts_input.text,
            language_code=tts_input.language_code,
            audio_file=temp_audio_path,  # Save the file path
            characters_used=len(tts_input.text),
            model_used="tts-1",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(tts_record)
        db.commit()
        db.refresh(tts_record)

        return create_response(
            success=True,
            message="Text-to-speech conversion successful",
            data={
                "file_url": f"{unique_filename}",  
                "characters_used": len(tts_input.text),
                "timestamp": tts_record.timestamp.isoformat(),
                "language_used": tts_record.language_code,
                "model_used": tts_record.model_used,
            }
        )
    except Exception as e:
        return create_response(
            success=False,
            message=f"Text-to-speech conversion failed: {str(e)}"
        )
    
from fastapi.responses import FileResponse

@router.get("/{filename}")
async def get_file(
    filename: str,
    current_user: str = Depends(get_current_user)
):
    file_path = f"./uploaded_audio/{filename}" 
    if os.path.exists(file_path):  
        return FileResponse(file_path) 
    return {"error": "File not found"}  

from uuid import uuid4
from pathlib import Path
import os

# Directory to save uploaded images
UPLOAD_DIR = "uploaded_images"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Mount static files for serving images
router.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@router.post("/upload-image", response_model=None)
def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Validate file type
        ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed."
            )

        # Generate unique filename
        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save the file
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # Create file URL
        file_url = f"/images/{unique_filename}"
        file_url = BASE_URL + file_url


        # Return the file URL in the response
        return create_response(
            success=True,
            message="Image uploaded successfully",
            data={"image_url": file_url}
        )
    except Exception as e:
        return create_response(
            success=False,
            message=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/images-to-text/", response_model=ImagesToTextOutput)
def images_to_text_endpoint(
    images_input: ImagesToTextInput,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Ensure image URLs have valid formats
        for image_url in images_input.image_urls:
            if not (image_url.lower().endswith((".png", ".jpeg", ".jpg", ".gif", ".webp"))):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format for URL: {image_url}. Supported formats: png, jpeg, jpg, gif, webp.",
                )

        # Prepare the request payload for OpenAI API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": images_input.prompt,
                    }
                ],
            }
        ]

        # Add the image URLs to the messages
        for image_url in images_input.image_urls:
            messages[0]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                }
            )

        # Call the OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
        )

        # Extract and format the response
        response_content = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens

        # Save the text response to the database
        new_response = ImagesToTextModel(
            text_response=response_content,
            model_used="gpt-4o-mini",
            token_used=tokens_used,
            language_used=images_input.language_code,
        )
        db.add(new_response)
        db.commit()

        return create_response(
            success=True,
            message="Image-to-text conversion successful",
            data={
                "text_response": response_content,
                "model_used": "gpt-4o-mini",
                "token_used": tokens_used,
                "language_used": images_input.language_code,
                "additional_data": {},
            }
        )

    except HTTPException as e:
        raise e  # Re-raise specific HTTPExceptions for proper client feedback
    except Exception as e:
        return create_response(
            success=False,
            message=f"Image-to-text conversion failed: {str(e)}",
        )

# from pydantic import BaseModel, AnyHttpUrl
# from typing import List

# class AnalyzeImageInput(BaseModel):
#     image_urls: List[AnyHttpUrl]  

# @router.post("/analyze-image/")
# def analyze_image_endpoint(
#     images_input: AnalyzeImageInput,
#     current_user: str = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     try:
#         # Ensure image URLs have valid formats
#         for image_url in images_input.image_urls:
#             image_url = str(image_url)  # Convert HttpUrl to string
#             if not image_url.lower().endswith((".png", ".jpeg", ".jpg", ".gif", ".webp")):
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Unsupported image format for URL: {image_url}. Supported formats: png, jpeg, jpg, gif, webp.",
#                 )

#         # Prepare the request payload for OpenAI API
#         messages = [
#             {
#                 "role": "user",
#                 "content": [{"type": "text", "text": "Describe the content of these images."}],
#             }
#         ]

#         # Convert AnyHttpUrl to string before adding to messages
#         for image_url in images_input.image_urls:
#             messages[0]["content"].append({"type": "image_url", "image_url": {"url": str(image_url)}})

#         # Call the OpenAI API for image analysis
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=messages,
#             max_tokens=300,
#         )

#         # Extract and format the response
#         analysis_result = response.choices[0].message.content.strip()
#         tokens_used = response.usage.total_tokens

#         # Generate insightful questions prompt
#         questions_prompt = f"Based on the provided images, generate 4 insightful questions that encourage further discussion.\n{analysis_result}"

#         # Prepare messages for generating questions
#         question_messages = [
#             {
#                 "role": "system",
#                 "content": "You are an AI assistant that analyzes images and provides meaningful insights."
#             },
#             {
#                 "role": "user",
#                 "content": [{"type": "text", "text": questions_prompt}]
#             }
#         ]

#         # Call OpenAI API to generate insightful questions
#         question_response = openai.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=question_messages,
#             max_tokens=150,
#         )

#         # Extract the questions from the response
#         questions = question_response.choices[0].message.content.strip()

#         return create_response(
#             success=True,
#             message="Image analysis successful",
#             data={
#                 "analysis_text": analysis_result,
#                 "suggested_questions": questions,
#                 "model_used": "gpt-4o-mini",
#                 "token_used": tokens_used,
#                 "additional_data": {},
#             },
#         )

#     except HTTPException as e:
#         raise e  # Re-raise specific HTTPExceptions for proper client feedback
#     except Exception as e:
#         return create_response(
#             success=False,
#             message=f"Image analysis failed: {str(e)}",
#         )
