from fastapi import FastAPI,Form, HTTPException, APIRouter, Depends, File, UploadFile
from schemas import QuestionInput, StructuredResponse, ChatResponse, SessionOneResponse, SessionResponse, SessionBase, SessionCreateResponse, ChatBase, ChatRequest, ChatTopicBasedRequest, SessionListResponse
from services.chat import get_all_sessions, convert_chat_history_to_dict, truncate_chat_history, summarize_history, calculate_tokens, save_chat_history
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from services.auth import get_current_user
import openai 
import os
from models import SessionModel, ChatModel, Topic, User
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from services.classes import create_response
from pydantic import BaseModel, Field, root_validator, EmailStr
import json
from typing import Optional, Dict, List
import logging
from openai import OpenAI
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("Missing OpenAI API key. Ensure it's set in the .env file.")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

MAX_HISTORY_TOKENS = 1000
MODEL = "gpt-4o-mini"

# Set up OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not openai_client.api_key:
    logger.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")


@router.post("/sessions/start", response_model=SessionCreateResponse)
async def start_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.user_id 

    session_id = str(uuid.uuid4())  
    new_session = SessionModel(
        id=session_id,
        user_id=user_id,
        status="active",
        started_at=datetime.utcnow() 
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return create_response(
        success=True,
        message="New session started successfully.",
        data={
            "session_id": str(new_session.id),
            "status": new_session.status,
            "started_at": new_session.started_at.isoformat()
        }
    )


@router.post("/ask-question/", response_model=None)
def ask_question(
    input: QuestionInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Handles a question input from the user and returns an answer with structured output.
    """
    logger.info("Received a question request")
    try:
        # Validate and convert session_id to UUID
        session_id = uuid.UUID(input.session_id)
    except ValueError:
        logger.error(f"Invalid session_id format: {input.session_id}")
        return create_response(success=False, message="Invalid session ID format.", data=None, status_code=400)

    # Validate session_id
    session = db.query(SessionModel).filter(
        SessionModel.id == input.session_id, SessionModel.status == "active"
    ).first()

    if not session:
        logger.error(f"Invalid or inactive session_id: {input.session_id}")
        return create_response(success=False, message="Invalid or inactive session ID.", data=None, status_code=400)
    
    # Update session details with new information
    session.title = f"{input.class_name} - {input.subject_name} - {input.chapter_name} - {input.topic_name}"
    session.last_message = input.question
    session.last_message_time = datetime.utcnow()
    db.commit()
    db.refresh(session)

    # Construct system and user messages
    system_message = {
        "role": "system",
        "content": (
            "You are an educational assistant. Extract the response as a structured JSON object "
            "with the fields: 'answer', 'details', and 'suggested_questions'."
        )
    }
    user_message = {
        "role": "user",
        "content": (
            f"Class: {input.class_name}, Subject: {input.subject_name}, "
            f"Chapter: {input.chapter_name}, Topic: {input.topic_name}. Question: {input.question}"
        )
    }
    messages = input.chat_history + [system_message, user_message]

    try:
        # Call the OpenAI API
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Replace with the correct model
            messages=messages,
            response_format=StructuredResponse,
        )

        structured_data = completion.choices[0].message.parsed
        usage_data = completion.usage  # This might be a custom object, so access directly

        input_tokens = usage_data.input_tokens if hasattr(usage_data, 'input_tokens') else None
        output_tokens = usage_data.output_tokens if hasattr(usage_data, 'output_tokens') else None
        model_used = "gpt-4o-mini"  # Update as required

        # Save the interaction in the database
        chat_entry = ChatModel(
            session_id=input.session_id,
            request_message=user_message["content"],
            response_message=structured_data.answer,
            status="active",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=model_used,
            timestamp=datetime.utcnow()
        )
        db.add(chat_entry)
        db.commit()

        return create_response(success=True, message="Question processed successfully.", data=structured_data.dict(), status_code=200)

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return create_response(success=False, message=f"OpenAI API error: {str(e)}", data=None, status_code=500)

@router.get("/sessions", response_model=None)
def get_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves a list of sessions for the current user.
    """
    try:
        user_id = current_user.user_id

        # Query sessions for the current user
        sessions = db.query(SessionModel).filter(
            SessionModel.user_id == user_id
        ).order_by(SessionModel.started_at.desc()).all()

        # Map sessions to response model
        session_list = [
            {
                "session_id": str(session.id),
                "title": session.title or "Untitled Session",
                "status": session.status,
                "last_message": session.last_message,
                "last_message_time": session.last_message_time.isoformat() if session.last_message_time else None,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            }
            for session in sessions
        ]

        return create_response(success=True, message="Session list retrieved successfully", data=session_list)

    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")



@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: uuid.UUID, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.status == "active").first()
        if not session:
            return create_response(success=False, message="Session not found or already deleted")
        session.status = "deleted"
        db.commit()
        return create_response(success=True, message=  "Session deleted successfully")
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")



@router.get("/sessions/{session_id}/chats", response_model=List[ChatResponse])
def get_chats_for_session(
    session_id: uuid.UUID, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    try:
        chats = db.query(ChatModel).filter(ChatModel.session_id == session_id, ChatModel.status == "active").order_by(ChatModel.timestamp).all()
        if not chats:
            return create_response(success=False, message="No chats found for this session")
        response_data = [
            {
                "session_id": str(chat.session_id),  
                "request_message": chat.request_message,
                "response_message": chat.response_message,
                "status": chat.status,
                "timestamp": chat.timestamp.isoformat()  
            }
            for chat in chats
        ]
        return create_response(success=True, message="Chats found for this session successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")


@router.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: uuid.UUID, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    try:
        chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.status == "active").first()
        if not chat:
            return create_response(success=False, message="Chat not found or already deleted")
        chat.status = "deleted"
        db.commit()
        return create_response(success=True, message= "Chat deleted successfully")
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")


# @router.post("/education/chat", response_model=None)
# async def education_chat(
#     request: ChatRequest, 
#     current_user: str = Depends(get_current_user), 
#     db: Session = Depends(get_db)
# ):
#     # user_id = current_user["id"]
#     user_id = current_user.user_id
#     session = db.query(SessionModel).filter(
#         SessionModel.user_id == user_id, SessionModel.status == "active"
#     ).first()

#     if not session:
#         session_id = str(uuid.uuid4())
#         new_session = SessionModel(
#             id=session_id,
#             user_id=user_id,
#             status="active",
#             started_at=datetime.utcnow()
#         )
#         db.add(new_session)
#         db.commit()
#         db.refresh(new_session)
#         session = new_session

#     existing_chat = db.query(ChatModel).filter(ChatModel.session_id == session.id).all()
#     chat_history_context = [
#         {
#             "user": chat.request_message,
#             "bot": chat.response_message
#         } for chat in existing_chat
#     ] if existing_chat else []

#     history_tokens = calculate_tokens(chat_history_context, model=MODEL)
#     if history_tokens > MAX_HISTORY_TOKENS:
#         truncated_history = truncate_chat_history(chat_history_context, MAX_HISTORY_TOKENS)
#         summarized_context = summarize_history(truncated_history)
#     else:
#         summarized_context = chat_history_context

#     prompt = f"""
#     ### Educational Insights
#     {summarized_context}

#     ### User Query
#     {request.request_message}

#     ### Response
#     Provide a knowledgeable and concise answer.
#     """

#     try:
#         response = openai.chat.completions.create(
#             model=MODEL,
#             messages=[{"role": "system", "content": prompt}],
#             max_tokens=500
#         )
#         bot_response = response.choices[0].message.content.strip()
#         input_tokens = calculate_tokens(request.request_message, model=MODEL)
#         output_tokens = calculate_tokens(bot_response, model=MODEL)

#         save_chat_history(
#             db, session.id, request.request_message, bot_response, input_tokens, output_tokens, MODEL
#         )

#         return create_response(
#             success=True,
#             message="Response generated successfully",
#             data={
#                 "session_id": str(session.id),
#                 "request_message": request.request_message,
#                 "response_message": bot_response,
#                 "input_tokens": input_tokens,
#                 "output_tokens": output_tokens,
#                 "status": "active",
#                 "model_used": MODEL,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
#         )
#     except Exception as e:
#         return create_response(success=False, message=f"Error: {str(e)}")