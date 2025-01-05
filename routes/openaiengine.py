import os
import uuid
import base64
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles


from dotenv import load_dotenv
import base64

import openai

load_dotenv()


from fastapi import APIRouter, Depends, HTTPException, status
router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for serving uploaded images
router.mount("/uploaded_images", StaticFiles(directory=UPLOAD_DIR), name="uploaded_images")

# Retrieve API keys from environment variable and split into a set
API_KEYS_ENV = os.getenv("API_KEYS")
if not API_KEYS_ENV:
    raise ValueError("API keys not found. Please set the API_KEYS environment variable.")

API_KEYS = set(API_KEYS_ENV.split(","))

def get_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key

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
def speech_to_text_endpoint(stt_input: STTInput, api_key: str = Depends(get_api_key)):
    audio_bytes = decode_base64(stt_input.audio_file)
    audio_time_in_sec = calculate_audio_duration(audio_bytes)
    temp_audio_path = f"temp_{uuid.uuid4()}.wav"
    with open(temp_audio_path, "wb") as f:
        f.write(audio_bytes)
    try:
        with open(temp_audio_path, "rb") as audio_file:
            # response = openai.audio.transcribe("whisper-1", audio_file, language=stt_input.language_code)
            response = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )

    except Exception as e:
        os.remove(temp_audio_path)
        raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")
    os.remove(temp_audio_path)
    audio_text = response.text
    print("audio_text",audio_text)
    model_used =  "whisper-1" #response.get("model", "whisper-1")
    language_code = "en" #response.get("language", stt_input.language_code)
    return STTOutput(
        audio_text=audio_text,
        audio_time_in_sec=audio_time_in_sec,
        model_used=model_used,
        language_code=language_code,
        timestamp=datetime.datetime.utcnow(),
        additional_data={}
    )

@router.post("/text-to-speech/", response_model=TTSOutput)
def text_to_speech_endpoint(tts_input: TTSInput, api_key: str = Depends(get_api_key)):
    characters_used = len(tts_input.text)
    try:

        # Create a chat completion with audio modality
        # completion = openai.chat.completions.create(
        #     model="gpt-4o-audio-preview",
        #     modalities=["text", "audio"],
        #     audio={"voice": "alloy", "format": "wav"},
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": tts_input.text
        #         }
        #     ]
        # )

        response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=tts_input.text
        )
        audio_content = b''.join(response.iter_bytes())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")

    # Extract the audio data from the response
    # try:
    #     audio_data_base64 = completion.choices[0].message.audio.data
    # except AttributeError:
    #     raise HTTPException(status_code=500, detail="Audio data not found in OpenAI response.")
    # except IndexError:
    #     raise HTTPException(status_code=500, detail="No choices returned in OpenAI response.")

    # Decode the Base64 audio data
    # try:
    #     audio_bytes = base64.b64decode(audio_content)
    # except Exception:
    #     raise HTTPException(status_code=500, detail="Failed to decode audio data.")

    # Optionally, save the audio to a file (e.g., for logging or debugging)
    # with open("output.wav", "wb") as f:
    #     f.write(audio_bytes)

    # Re-encode to Base64 for the response
    audio_base64 = encode_base64(audio_content)

    return TTSOutput(
        audio_file=audio_base64,
        characters_used=characters_used,
        timestamp=datetime.datetime.utcnow(),
        language_used=tts_input.language_code,
        model_used="gpt-4o-audio-preview",
        additional_data={}
    )


@router.post("/upload-image/", response_model=UploadImageOutput)
def upload_image_endpoint(files: List[UploadFile] = File(...), x_api_key: Optional[str] = Header(None)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")
    image_urls = []
    for file in files:
        if file.content_type not in ["image/png", "image/jpeg", "image/jpg", "image/gif"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        image_url = f"/uploaded_images/{unique_filename}"
        image_urls.routerend(image_url)
    return UploadImageOutput(image_urls=image_urls)

@router.post("/images-to-text/", response_model=ImagesToTextOutput)
def images_to_text_endpoint(images_input: ImagesToTextInput, api_key: str = Depends(get_api_key)):
    try:
        response = openai.images.generate(prompt=images_input.prompt,
        images=images_input.image_urls,
        model="vision-model-1")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")
    text_response = response.get("text", "")
    model_used = response.get("model", "vision-model-1")
    token_used = response.get("usage", {}).get("total_tokens", 0)
    language_used = images_input.language_code
    return ImagesToTextOutput(
        text_response=text_response,
        model_used=model_used,
        token_used=token_used,
        language_used=language_used,
        additional_data={}
    )
