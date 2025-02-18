from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from database import get_db
from utils.auth import get_current_user
from services.chat import (
    start_new_session,
    process_question,
    fetch_sessions,
    remove_session,
    fetch_chats_for_session,
    remove_chat
)
from schemas.chat import QuestionInput
from schemas.session import SessionCreateResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sessions/start", response_model=SessionCreateResponse)
async def start_session(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return start_new_session(db, current_user)


@router.post("/ask-question/")
def ask_question(
    input: QuestionInput,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return process_question(input, db, current_user)


@router.get("/sessions")
def get_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return fetch_sessions(db, current_user)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return remove_session(db, session_id)


@router.get("/sessions/{session_id}/chats")
def get_chats_for_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return fetch_chats_for_session(db, session_id)


@router.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return remove_chat(db, chat_id)
