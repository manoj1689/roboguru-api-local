from fastapi import FastAPI,Form, HTTPException, APIRouter, Depends, File, UploadFile
from schemas import ChatResponse, SessionResponse, SessionBase, SessionCreateResponse, ChatBase, ChatRequest, ChatTopicBasedRequest
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


@router.post("/education/chat", response_model=None)
async def education_chat(
    request: ChatRequest, 
    current_user: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # user_id = current_user["id"]
    user_id = current_user.user_id
    session = db.query(SessionModel).filter(
        SessionModel.user_id == user_id, SessionModel.status == "active"
    ).first()

    if not session:
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
    {summarized_context}

    ### User Query
    {request.request_message}

    ### Response
    Provide a knowledgeable and concise answer.
    """

    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=500
        )
        bot_response = response.choices[0].message.content.strip()
        input_tokens = calculate_tokens(request.request_message, model=MODEL)
        output_tokens = calculate_tokens(bot_response, model=MODEL)

        save_chat_history(
            db, session.id, request.request_message, bot_response, input_tokens, output_tokens, MODEL
        )

        return create_response(
            success=True,
            message="Response generated successfully",
            data={
                "session_id": str(session.id),
                "request_message": request.request_message,
                "response_message": bot_response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "status": "active",
                "model_used": MODEL,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        return create_response(success=False, message=f"Error: {str(e)}")

@router.post("/sessions/start", response_model=SessionCreateResponse)
async def start_session(
    current_user: User = Depends(get_current_user),  # Ensure this gets the current user
    db: Session = Depends(get_db)
):
    """
    Starts a new session for the user when they access the chat window.
    """
    user_id = current_user.user_id  # Get the user_id from the current_user object

    # Check if the user exists in the "users" table (we already have this check from get_current_user)
    if not current_user:
        return create_response(
            success=False,
            message="User not found.",
            data=None
        )

    # Check if the user already has an active session
    existing_session = db.query(SessionModel).filter(
        SessionModel.user_id == user_id, SessionModel.status == "active"
    ).first()

    if existing_session:
        return create_response(
            success=False,
            message="You already have an active session.",
            data={"session_id": str(existing_session.id), "status": existing_session.status}
        )

    # Create a new session
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

# Models for request and response
class QuestionInput(BaseModel):
    session_id: str
    class_name: str
    subject_name: str
    chapter_name: str
    topic_name: str
    question: str
    chat_history: Optional[List[Dict[str, str]]] = []  # [{'role': 'user', 'content': '...'}, ...]

class StructuredResponse(BaseModel):
    answer: str
    details: str
    suggested_questions: List[str]

    def to_dict_list(self):
        return [{kvp.key: kvp.value} for kvp in self.items]

class APIResponse(BaseModel):
    error: Optional[str]
    data: Optional[StructuredResponse]

class HealthCheckResponse(BaseModel):
    error: Optional[str]
    data: Dict[str, str]

@router.post("/ask-question/", response_model=APIResponse)
def ask_question(
    input: QuestionInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Handles a question input from the user and returns an answer with structured output.
    """
    logger.info("Received a question request")

    # Validate session_id
    session = db.query(SessionModel).filter(
        SessionModel.id == input.session_id, SessionModel.status == "active"
    ).first()

    if not session:
        logger.error(f"Invalid or inactive session_id: {input.session_id}")
        return APIResponse(error="Invalid or inactive session ID.", data=None)

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
        input_tokens = completion.usage.input_tokens
        output_tokens = completion.usage.output_tokens
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

        return APIResponse(error=None, data=structured_data)

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return APIResponse(error=f"OpenAI API error: {str(e)}", data=None)
















# @router.post("/ask-question/", response_model=APIResponse)
# # @router.post("/ask-question/")

# def ask_question(input: QuestionInput):
#     """
#     Handles a question input from the user and returns an answer with structured output.
#     """
#     logger.info("Received a question request")

#     # Construct system and user messages
#     system_message = {
#         "role": "system",
#         "content": (
#             "You are an educational assistant. Extract the response as a structured JSON object "
#             "with the fields: 'answer', 'details', and 'suggested_questions'."
#         )
#     }
#     user_message = {
#         "role": "user",
#         "content": (
#             f"Class: {input.class_name}, Subject: {input.subject_name}, "
#             f"Chapter: {input.chapter_name}, Topic: {input.topic_name}. Question: {input.question}"
#         )
#     }
#     messages = input.chat_history + [system_message, user_message]

#     try:
#         # Use OpenAI's structured response parsing
#         completion = openai_client.beta.chat.completions.parse(
#             model="gpt-4o-mini",  # Replace with the required model
#             messages=messages,
#             response_format=StructuredResponse,
#         )

#         structured_data = completion.choices[0].message.parsed

#         # logger.info("Question processed successfully")
#         return APIResponse(error=None, data=structured_data)
    

#      # Log the data in proper JSON format so you can see what's really being returned
#         # response_obj = APIResponse(error=None, data=structured_data)
#         # response_obj = json.dumps(response_obj.dict(), indent=2)
#         # logger.info("Returning response to client:\n%s", response_obj)
#         # # Return a valid APIResponse object (FastAPI automatically serializes this as JSON)
#         # return response_obj


#     except Exception as e:
#         logger.error(f"Error processing question: {str(e)}")
#         return APIResponse(error=f"OpenAI API error: {str(e)}", data=None)



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


