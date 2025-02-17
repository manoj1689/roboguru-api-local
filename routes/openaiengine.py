import os
import uuid
import base64
from datetime import datetime
from typing import List
from fastapi import status, APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from models import STTModel, ImageModel, ImagesToTextModel, TTSModel, User
from sqlalchemy.orm import Session
from database import get_db
from services.auth import get_current_user 
from services.classes import create_response
from dotenv import load_dotenv
from schemas import STTInput, STTOutput, TTSInput, TTSOutput, ImagesToTextInput, ImagesToTextOutput
import openai
from pathlib import Path

load_dotenv()

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

BASE_URL = os.getenv("BASE_URL")

# Directory setup
UPLOAD_DIR = "uploaded_images"
TTS_UPLOAD_DIR = "uploaded_audio"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(TTS_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

router.mount("/uploaded_audio", StaticFiles(directory=TTS_UPLOAD_DIR), name="uploaded_audio")
router.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

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
        audio_bytes = decode_base64(stt_input.audio_file)
        audio_time_in_sec = calculate_audio_duration(audio_bytes)

        temp_audio_path = f"{UPLOAD_DIR}/temp_{uuid.uuid4()}.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes)

        with open(temp_audio_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )

        os.remove(temp_audio_path)

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

@router.post("/text-to-speech/", response_model=TTSOutput)
def text_to_speech_endpoint(
    tts_input: TTSInput,
    current_user: str = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=tts_input.text
        )
        audio_content = b''.join(response.iter_bytes())

        unique_filename = f"tts_{uuid.uuid4()}.wav"
        temp_audio_path = os.path.join(TTS_UPLOAD_DIR, unique_filename)
        with open(temp_audio_path, "wb") as f:
            f.write(audio_content)

        audio_base64 = encode_base64(audio_content)

        tts_record = TTSModel(
            text=tts_input.text,
            language_code=tts_input.language_code,
            audio_file=temp_audio_path,
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

@router.get("/{filename}")
async def get_file(
    filename: str,
    current_user: str = Depends(get_current_user)
):
    file_path = f"./uploaded_audio/{filename}" 
    if os.path.exists(file_path):  
        return FileResponse(file_path) 
    return {"error": "File not found"}  

@router.post("/upload-image", response_model=None)
def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed."
            )

        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        file_url = BASE_URL + f"/images/{unique_filename}"

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
        for image_url in images_input.image_urls:
            if not (image_url.lower().endswith((".png", ".jpeg", ".jpg", ".gif", ".webp"))):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported image format for URL: {image_url}. Supported formats: png, jpeg, jpg, gif, webp.",
                )

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

        for image_url in images_input.image_urls:
            messages[0]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                }
            )

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
        )

        response_content = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens

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
        raise e
    except Exception as e:
        return create_response(
            success=False,
            message=f"Image-to-text conversion failed: {str(e)}",
        )