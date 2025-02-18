import os
import openai
import base64
from fastapi import HTTPException
from typing import List

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")


def decode_base64(encoded_str: str) -> bytes:
    try:
        return base64.b64decode(encoded_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 string.")


def encode_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")


def calculate_audio_duration(audio_bytes: bytes, sample_rate: int = 16000) -> float:
    return len(audio_bytes) / (sample_rate * 2)  # Assuming 16-bit audio


def transcribe_audio(audio_path: str) -> str:
    try:
        with open(audio_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")


def generate_speech(text: str) -> bytes:
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        return b''.join(response.iter_bytes())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")


def process_image_to_text(image_urls: List[str], prompt: str):
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    for image_url in image_urls:
        messages[0]["content"].append({"type": "image_url", "image_url": {"url": image_url}})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip(), response.usage.total_tokens
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image-to-text: {str(e)}")
