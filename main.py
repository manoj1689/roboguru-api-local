from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, get_db  
import models
from routes import (
    questions, user_progress, search, firebase, classes, subjects, chapters,
    topics, login, chat, level, users, trending, openaiengine
)
from services.users import create_superadmin
from utils.exception_handlers import custom_http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from core.config import settings 

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Parent directory for uploads
UPLOAD_DIR = "uploads"
UPLOADS_IMAGES_DIR = f"{UPLOAD_DIR}/images"
TTS_UPLOAD_DIR = f"{UPLOAD_DIR}/audio"
UPLOADS_PROFILE_DIR = f"{UPLOAD_DIR}/profile_images"

# Ensure directories exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOADS_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(TTS_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOADS_PROFILE_DIR).mkdir(parents=True, exist_ok=True)

# Mount static files for serving uploaded content
app.mount("/uploads/images", StaticFiles(directory=UPLOADS_IMAGES_DIR), name="images")
app.mount("/uploads/audio", StaticFiles(directory=TTS_UPLOAD_DIR), name="audio")
app.mount("/uploads/profile_images", StaticFiles(directory=UPLOADS_PROFILE_DIR), name="profile_images")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Register Exception Handler
app.add_exception_handler(HTTPException, custom_http_exception_handler)

# Include Routers
app.include_router(login.router, tags=["login"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(level.router, prefix="/level", tags=["level"])
app.include_router(classes.router, prefix="/classes", tags=["classes"])
app.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
app.include_router(chapters.router, prefix="/chapters", tags=["chapters"])
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(trending.router, prefix="/trending", tags=["trending"])
app.include_router(openaiengine.router, prefix="/openaiengine", tags=["openaiengine"])
app.include_router(firebase.router, prefix="/firebase", tags=["firebase"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(user_progress.router, prefix="/user_progress", tags=["user_progress"])
app.include_router(questions.router, prefix="/exams", tags=["examinations"])

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    create_superadmin(db)

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "running", "database_url": settings.SQLALCHEMY_DATABASE_URL}
