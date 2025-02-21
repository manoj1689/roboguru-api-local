from fastapi import APIRouter

from routes import (
    login, users, level, classes, subjects, chapters, topics, chat, trending, 
    openaiengine, firebase, search, user_progress, questions
)

router = APIRouter()

router.include_router(login.router, tags=["login"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(level.router, prefix="/level", tags=["level"])
router.include_router(classes.router, prefix="/classes", tags=["classes"])
router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])
router.include_router(chapters.router, prefix="/chapters", tags=["chapters"])
router.include_router(topics.router, prefix="/topics", tags=["topics"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(trending.router, prefix="/trending", tags=["trending"])
router.include_router(openaiengine.router, prefix="/openaiengine", tags=["openaiengine"])
router.include_router(firebase.router, prefix="/firebase", tags=["firebase"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(user_progress.router, prefix="/user_progress", tags=["user_progress"])
router.include_router(questions.router, prefix="/exams", tags=["examinations"])
