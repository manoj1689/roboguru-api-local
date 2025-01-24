from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, get_db
import models
from routes import user_progress, search, firebase, classes, subjects, chapters, topics, login, chat, level, users, trending, openaiengine
from services.users import create_superadmin
from exception_handlers import custom_http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

import os
# Directory to save uploaded images
UPLOAD_DIR = "uploaded_profile_images"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Mount static files for serving profile images
app.mount("/profile_images", StaticFiles(directory="uploaded_profile_images"), name="profile_images")


# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
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





@app.on_event("startup")
def on_startup():
    db = next(get_db())
    create_superadmin(db)












# from fastapi.responses import JSONResponse
# # Fetch subjects by class_id
# @app.get("/subjects/{class_id}", response_class=JSONResponse)
# async def get_subjects(class_id: int, db: Session = Depends(get_db)):
#     subjects = services.subjects.get_subjects_by_class(db=db, class_id=class_id)
#     return subjects

# # Fetch chapters by subject_id
# @app.get("/chapters/{subject_id}", response_class=JSONResponse)
# async def get_chapters(subject_id: int, db: Session = Depends(get_db)):
#     chapters = services.chapters.get_chapters_by_subject(db=db, subject_id=subject_id)
#     return chapters

# # Fetch topics by chapter_id
# @app.get("/topics/{chapter_id}", response_class=JSONResponse)
# async def get_topics(chapter_id: int, db: Session = Depends(get_db)):
#     topics = services.topics.get_topics_by_chapter(db=db, chapter_id=chapter_id)
#     return topics