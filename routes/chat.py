from fastapi import FastAPI,Form, HTTPException, APIRouter, Depends, File, UploadFile
from schemas import QuestionInput, ChatStructuredResponse, ChatResponse, SessionOneResponse, SessionResponse, SessionBase, SessionCreateResponse, ChatBase, ChatRequest, ChatTopicBasedRequest, SessionListResponse
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
import re 
import tiktoken

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("Missing OpenAI API key. Ensure it's set in the .env file.")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

MAX_HISTORY_TOKENS = 1000
MODEL = "gpt-4o"
TOKEN_LIMIT = 300
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

@router.post("/ask-question/")
def ask_question(
    input: QuestionInput,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        session_id = uuid.UUID(input.session_id)
    except ValueError:
        return create_response(success=False, message="Invalid session ID format.", data=None, status_code=400)

    session = db.query(SessionModel).filter(
        SessionModel.id == input.session_id, SessionModel.status == "active"
    ).with_for_update().first()

    if not session:
        return create_response(success=False, message="Invalid or inactive session ID.", data=None, status_code=400)

    # Ensure chat_summary is not None (to prevent null responses)
    chat_summary = input.chat_summary if input.chat_summary else session.chat_summary
    if chat_summary is None:
        chat_summary = ""


    # System instructions for AI
    system_message = {
        "role": "system",
        "content": (
            "You are an AI-powered educational assistant designed to help students learn effectively. "
            # "Provide clear, concise, and well-structured answers tailored to the question's topic. "
            "Use the following guidelines:\n"
            "- Highlight important terms using **bold** text.\n"
            "- Use _italics_ for emphasis when necessary.\n"
            "- For explanations, use bullet points or numbered lists to organize content:\n"
            "  - Use `-` or `*` for bullet points.\n"
            "  - Use `1.`, `2.`, `3.` for numbered lists.\n"
            "- Provide examples where relevant to enhance understanding.\n"
            "- Include links or references for further learning in Markdown format, such as:\n"
            "  `[Click here](https://example.com)`.\n"
            "- Use Markdown headers (e.g., `#`, `##`, `###`) for headings to structure the content.\n"
            "- Avoid overly complex language; aim for simplicity and readability.\n"
            "- Ensure responses are engaging and well-structured by leveraging Markdown formatting.\n"
            "- Maintain an educational tone, using structured content, examples, and diagrams where applicable.\n"
            "- Responses should include headings, paragraphs, and lists where appropriate.\n"
            "- Suggest related questions for further exploration using bullet points.\n"
            "- Answer the question and **update the chat summary** by integrating the response into the conversation history.\n"
            "- The chat summary should **evolve dynamically** based on previous interactions, the user's current question, and the AI-generated response."
            "- If the user asks irrelevant, non-educational, or off-topic questions, provide a polite, simple response, such as:\n"
            "  - 'You're welcome!'\n"
            "  - 'I can't process that request right now.'\n"
            "  - 'Please ask an educational question.'\n"
            "- These responses should be brief and acknowledge the user's statement without further elaboration."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Class: {input.class_name}, Subject: {input.subject_name}, "
            f"Chapter: {input.chapter_name}, Topic: {input.topic_name}.\n\n"
            f"Question: {input.question}\n\n"
            f"Previous Chat Summary:\n{chat_summary if chat_summary else 'None'}"
        )
    }
    # Construct AI message to update chat summary
    update_summary_prompt = {
        "role": "assistant",
        "content": (
            "Based on the previous chat summary and the new question, generate an updated chat summary "
            "that retains relevant past information, incorporates the AI response, and ensures the conversation context is maintained."
        )
    }
    messages = [system_message, user_message, update_summary_prompt]

    try:
        # 🔹 Call OpenAI API
        completion = openai_client.beta.chat.completions.parse(
            model=MODEL,
            messages=messages,
            response_format=ChatStructuredResponse,
        )

        if not completion.choices:
            return create_response(success=False, message="No response received from OpenAI.", data=None, status_code=500)

        structured_data = completion.choices[0].message.parsed
        usage_data = completion.usage

        input_tokens = getattr(usage_data, "input_tokens", 0)
        output_tokens = getattr(usage_data, "output_tokens", 0)

        suggested_questions = getattr(structured_data, "suggested_questions", [])

        # Update chat_summary (use previous one if OpenAI returns None)
        new_chat_summary = structured_data.chat_summary if structured_data.chat_summary else chat_summary

        # Save chat entry in the database
        chat_entry = ChatModel(
            session_id=input.session_id,
            request_message=input.question,
            response_message=structured_data.answer,
            status="active",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_used=MODEL,
            timestamp=datetime.utcnow()
        )
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)

        # Update session metadata
        session.last_message = structured_data.answer
        session.last_message_time = datetime.utcnow()
        session.title = f"{input.class_name} - {input.subject_name} - {input.chapter_name} - {input.topic_name}"
        session.chat_summary = new_chat_summary  
        db.commit()
        db.refresh(session)

        return create_response(
            success=True,
            message="Question processed successfully.",
            data={
                "answer": structured_data.answer,
                "suggested_questions": suggested_questions,
                "chat_summary": new_chat_summary  
            },
            status_code=200
        )

    except Exception as e:
        logger.error(f"OpenAI API Error: {str(e)}")
        return create_response(success=False, message=f"OpenAI API error: {str(e)}", data=None, status_code=500)

@router.get("/sessions", response_model=None)
def get_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves a list of sessions for the current user excluding 'last_message is none Session'.
    Deletes 'last_message is none Session' records if found.
    """
    try:
        user_id = current_user.user_id

        sessions = db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.last_message != None
        ).order_by(SessionModel.started_at.desc()).all()

        session_list = []
        for session in sessions:
            title = session.title or "Unknown" 
            title_parts = title.split(" - ")

            class_name = title_parts[0] if len(title_parts) > 0 else "Unknown"
            subject_name = title_parts[1] if len(title_parts) > 1 else "Unknown"
            chapter_name = title_parts[2] if len(title_parts) > 2 else "Unknown"
            topic = title_parts[3] if len(title_parts) > 3 else title
            session_list.append({
                "session_id": str(session.id),
                "class_name": class_name,
                "subject_name": subject_name,
                "chapter_name": chapter_name,
                "topic": topic,
                "title": topic,
                "status": session.status,
                "last_message": session.last_message,
                "last_message_time": session.last_message_time.isoformat() if session.last_message_time else None,
                "started_at": session.started_at,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            })
        session_list.sort(key=lambda x: (x["title"] == "Unknown", -x["started_at"].timestamp()))

        for session in session_list:
            session["started_at"] = session["started_at"].isoformat()
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

@router.get("/sessions/{session_id}/chats", response_model=dict)
def get_chats_for_session(
    session_id: uuid.UUID, 
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user)
):
    try:
        chats = db.query(ChatModel).filter(
            ChatModel.session_id == session_id,
            ChatModel.status == "active"
            ).order_by(ChatModel.timestamp
        ).all()
        if not chats:
            return create_response(success=False, message="No chats found for this session")

        print(chats)
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

        title = session.title or "Unknown" 
        title_parts = title.split(" - ")

        class_name = title_parts[0] if len(title_parts) > 0 else "Unknown"
        subject_name = title_parts[1] if len(title_parts) > 1 else "Unknown"
        chapter_name = title_parts[2] if len(title_parts) > 2 else "Unknown"
        topic = title_parts[3] if len(title_parts) > 3 else title

        response_data = []

        for chat in chats:
            response_data.append(
                {"role": "user", "content": chat.request_message}
            )
            response_data.append(
                {"role": "assistant", "content": chat.response_message}
            )

        return {
            "success": True,
            "message": "Chats found for this session successfully",
            "session_id": str(session_id),
            "class_name": class_name,
            "subject_name": subject_name,
            "chapter_name": chapter_name,
            "topic_name": topic,
            "data": response_data
        }
    
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

from pydantic import BaseModel, AnyHttpUrl
from typing import List, Optional

class AnalyzeImageInput(BaseModel):
    session_id: str  
    question: str
    image_urls: Optional[List[AnyHttpUrl]] = [] 
    chat_summary: Optional[str] = None 

@router.post("/analyze-image/")
def analyze_image_endpoint(
    images_input: AnalyzeImageInput,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        session_id = uuid.UUID(images_input.session_id)
    except ValueError:
        return create_response(success=False, message="Invalid session ID format.", data=None, status_code=400)

    # Validate session_id
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id, SessionModel.status == "active"
    ).first()

    if not session:
        return create_response(success=False, message="Invalid or inactive session ID.", data=None, status_code=400)

    # Use previous chat summary if not provided in request
    chat_summary = images_input.chat_summary if images_input.chat_summary else session.chat_summary
    if chat_summary is None:
        chat_summary = ""

    # System message with updated instructions
    system_message = {
        "role": "system",
        "content": (
            "You are an AI-powered educational assistant. "
            "Analyze images (if provided) and answer the user's question in an educational way. "
            "If no images are sent, continue the discussion using previous context stored in the chat summary.\n\n"
            "- The latest response (from image analysis or text-based discussion).\n"
            "- The previous chat summary."
        )
    }

    # Step 1: **Handle Image Analysis (if images are provided)**
    analysis_result = "No images provided for analysis."
    if images_input.image_urls:
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": "Describe the content of these images."}]
        }

        for image_url in images_input.image_urls:
            user_message["content"].append({"type": "image_url", "image_url": {"url": str(image_url)}})

        messages = [system_message, user_message]

        try:
            # Call OpenAI API for image analysis
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
            )
            analysis_result = response.choices[0].message.content.strip()
        except openai.error.OpenAIError as e:
            return create_response(success=False, message="AI processing error.", data=None, status_code=500)

    # Step 2: **If no images are sent, generate a response using previous chat summary**
    elif chat_summary:
        messages = [
            system_message,
            {
                "role": "user",
                "content": f"Previous chat summary:\n{chat_summary}\n\nUser's Question:\n{images_input.question}\n\n"
                           "Continue the discussion based on previous context."
            }
        ]
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
            )
            analysis_result = response.choices[0].message.content.strip()
        except openai.error.OpenAIError as e:
            return create_response(success=False, message="AI processing error.", data=None, status_code=500)
    else:
        analysis_result = "No images or previous context available. Please provide more details."

    # Step 3: **Update Chat Summary**
    summary_messages = [
        system_message,
        {
            "role": "user",
            "content": f"Previous chat summary:\n{chat_summary}\n\nUser's Question:\n{images_input.question}\n\nAnalysis result:\n{analysis_result}"
        },
        {
            "role": "assistant",
            "content": "Based on the previous chat summary, user's question, and the new analysis result, generate an updated chat summary."
        }
    ]

    try:
        summary_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=summary_messages,
            max_tokens=300,
        )
        new_chat_summary = summary_response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        return create_response(success=False, message="AI processing error.", data=None, status_code=500)

    # Step 4: **Generate Suggested Questions**
    suggested_question_messages = [
        system_message,
        {
            "role": "user",
            "content": (
                f"User's question: '{images_input.question}'\n\n"
                f"Analysis result: '{analysis_result}'\n\n"
                "Generate 4 insightful follow-up questions based on the above information."
            )
        }
    ]

    try:
        question_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=suggested_question_messages,
            max_tokens=200,
        )
        suggested_questions = question_response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        return create_response(success=False, message="AI processing error.", data=None, status_code=500)

    # Step 5: **Save Updated Chat Summary**
    session.chat_summary = new_chat_summary
    session.last_message = analysis_result if images_input.image_urls else images_input.question
    session.last_message_time = datetime.utcnow()
    db.commit()
    db.refresh(session)

    # Step 6: **Return only necessary data**
    return create_response(
        success=True,
        message="Analysis completed successfully.",
        data={
            "analysis_result": analysis_result,
            "suggested_questions": suggested_questions, 
            "chat_summary": new_chat_summary  
        },
        status_code=200
    )
