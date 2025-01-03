from fastapi import FastAPI,Form, HTTPException, APIRouter, Depends, File, UploadFile
from schemas import ChatResponse, SessionResponse, SessionBase, ChatBase, ChatRequest
from services.chat import get_all_sessions, convert_chat_history_to_dict, truncate_chat_history, summarize_history, calculate_tokens, save_chat_history
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from services.auth import get_current_user
import openai 
import os
from models import SessionModel, ChatModel
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from services.classes import create_response


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("Missing OpenAI API key. Ensure it's set in the .env file.")

router = APIRouter()

MAX_HISTORY_TOKENS = 1000
MODEL = "gpt-4o-mini"


@router.post("/education/chat", response_model=None)
async def education_chat(
    request: ChatRequest, 
    current_user: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    user_id = current_user["id"]

    # Check for existing active session
    session = db.query(SessionModel).filter(
        SessionModel.user_id == user_id, SessionModel.status == "active"
    ).first()

    if not session:
        # Create a new session if none exists
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
        session = new_session

    existing_chat = db.query(ChatModel).filter(ChatModel.session_id == session.id).all()

    chat_history_context = [
        {
            "user": chat.request_message,
            "bot": chat.response_message
        } for chat in existing_chat
    ] if existing_chat else []

    history_tokens = calculate_tokens(chat_history_context, model=MODEL)
    if history_tokens > MAX_HISTORY_TOKENS:
        truncated_history = truncate_chat_history(chat_history_context, MAX_HISTORY_TOKENS)
        summarized_context = summarize_history(truncated_history)
    else:
        summarized_context = chat_history_context

    prompt = f"""
    ### Educational Insights
    The user has asked an educational question. 

    ### Chat History Summary
    {summarized_context}  

    ### User Query
    {request.request_message}  

    ### Response
    Provide a knowledgeable, concise, and direct answer to the user's educational question.
    The AI knows everything related to education and learning.
    """

    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=500
        )
        bot = response.choices[0].message.content.strip()

        # Save chat history to the database
        save_chat_history(db, session.id, request.request_message, bot)

        # Return JSON-serializable response
        return create_response(
            success=True,
            message="Educational response generated successfully",
            data={
                "session_id": str(session.id),  
                "request_message": request.request_message,
                "response_message": bot,
                "status": "active",
                "timestamp": datetime.utcnow().isoformat()  
            }
        )
    except Exception as e:
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












































# @router.get("/chat_history")
# async def get_chat_history_endpoint(
#     db: Session = Depends(get_db), 
#     current_user: str = Depends(get_current_user)
# ):
#     """
#     Fetch chat history for the authorized user.
#     """
#     user_id = current_user["id"]

#     chat_history_list = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
    
#     chat_history_data = convert_chat_history_to_dict(chat_history_list)
    
#     return {"chat_history": chat_history_data}


