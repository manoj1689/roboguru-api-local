from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from utils.auth import get_current_user
from services.openaiengine import (
    process_speech_to_text,
    process_text_to_speech,
    get_audio_file,
    upload_image,
    process_images_to_text
)
from schemas import STTInput, STTOutput, TTSInput, TTSOutput, ImagesToTextInput, ImagesToTextOutput
from fastapi.responses import FileResponse

router = APIRouter()


@router.post("/speech-to-text/", response_model=STTOutput)
def speech_to_text_endpoint(
    stt_input: STTInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return process_speech_to_text(stt_input, db)


@router.post("/text-to-speech/", response_model=TTSOutput)
def text_to_speech_endpoint(
    tts_input: TTSInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return process_text_to_speech(tts_input, db)


@router.get("/{filename}")
def get_file(filename: str, current_user: str = Depends(get_current_user)):
    file_path = get_audio_file(filename)
    return FileResponse(file_path)


@router.post("/upload-image/")
def upload_image_endpoint(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    return upload_image(file)


@router.post("/images-to-text/", response_model=ImagesToTextOutput)
def images_to_text_endpoint(
    images_input: ImagesToTextInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return process_images_to_text(images_input, db)
