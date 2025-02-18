import os
import uuid
from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from pathlib import Path
from models.stt import STTModel
from models.itt import ImagesToTextModel
from models.tts import TTSModel
from dotenv import load_dotenv
from schemas.stt_tts import STTInput, TTSInput
from schemas.image_processing import ImagesToTextInput
from utils.response import create_response
from utils.openaiengine import decode_base64, calculate_audio_duration, transcribe_audio, generate_speech, process_image_to_text

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

# Unified Uploads Directory
UPLOAD_DIR = "uploads"
UPLOADS_IMAGES_DIR = f"{UPLOAD_DIR}/images"
TTS_UPLOAD_DIR = f"{UPLOAD_DIR}/audio"

# Ensure Directories Exist
Path(UPLOADS_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(TTS_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def process_speech_to_text(stt_input: STTInput, db: Session):
    try:
        audio_bytes = decode_base64(stt_input.audio_file)
        audio_time_in_sec = calculate_audio_duration(audio_bytes)

        temp_audio_path = f"{TTS_UPLOAD_DIR}/temp_{uuid.uuid4()}.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(audio_bytes)

        transcription = transcribe_audio(temp_audio_path)

        os.remove(temp_audio_path)

        stt_output = STTModel(
            audio_file=temp_audio_path,
            language_code=stt_input.language_code,
            audio_text=transcription,
            audio_time_in_sec=audio_time_in_sec,
            model_used="whisper-1",
            timestamp=datetime.utcnow()
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
        return create_response(success=False, message=f"Speech-to-text conversion failed: {str(e)}")


def process_text_to_speech(tts_input: TTSInput, db: Session):
    try:
        unique_filename = f"tts_{uuid.uuid4()}.wav"
        temp_audio_path = os.path.join(TTS_UPLOAD_DIR, unique_filename)

        audio_content = generate_speech(tts_input.text)
        with open(temp_audio_path, "wb") as f:
            f.write(audio_content)

        tts_record = TTSModel(
            text=tts_input.text,
            language_code=tts_input.language_code,
            audio_file=temp_audio_path,
            characters_used=len(tts_input.text),
            model_used="tts-1",
            timestamp=datetime.utcnow()
        )
        db.add(tts_record)
        db.commit()
        db.refresh(tts_record)

        return create_response(
            success=True,
            message="Text-to-speech conversion successful",
            data={
                "file_url": unique_filename,
                "characters_used": len(tts_input.text),
                "timestamp": tts_record.timestamp.isoformat(),
                "language_used": tts_record.language_code,
                "model_used": tts_record.model_used,
            }
        )
    except Exception as e:
        return create_response(success=False, message=f"Text-to-speech conversion failed: {str(e)}")


def get_audio_file(filename: str):
    file_path = os.path.join(TTS_UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return file_path
    raise HTTPException(status_code=404, detail="File not found")


def upload_image(file: UploadFile):
    try:
        ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.")

        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOADS_IMAGES_DIR, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        file_url = f"{BASE_URL}/uploads/images/{unique_filename}"
        return create_response(success=True, message="Image uploaded successfully", data={"image_url": file_url})
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")


def process_images_to_text(images_input: ImagesToTextInput, db: Session):
    try:
        response_content, tokens_used = process_image_to_text(images_input.image_urls, images_input.prompt)

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
    except Exception as e:
        return create_response(success=False, message=f"Image-to-text conversion failed: {str(e)}")
