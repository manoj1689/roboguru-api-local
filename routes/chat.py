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


# @router.post("/ask-question/", response_model=None)
# def ask_question(
#     input: QuestionInput,
#     db: Session = Depends(get_db),
#     current_user: str = Depends(get_current_user)
# ):
#     """
#     Handles a question input from the user and returns an answer with structured output.
#     """
#     logger.info("Received a question request")
    
#     # Validate and convert session_id to UUID
#     try:
#         session_id = uuid.UUID(input.session_id)
#     except ValueError:
#         logger.error(f"Invalid session_id format: {input.session_id}")
#         return create_response(success=False, message="Invalid session ID format.", data=None, status_code=400)

#     # Validate session_id
#     session = db.query(SessionModel).filter(
#         SessionModel.id == input.session_id, SessionModel.status == "active"
#     ).first()

#     if not session:
#         logger.error(f"Invalid or inactive session_id: {input.session_id}")
#         return create_response(success=False, message="Invalid or inactive session ID.", data=None, status_code=400)
    

#     # Construct system and user messages
#     system_message = {
#         "role": "system",
#         "content": (
#             "You are an AI-powered educational assistant designed to help students learn effectively. "
#             "Provide clear, concise, and well-structured answers tailored to the question's topic. "
#             "Use the following guidelines:\n"
#             "- Highlight important terms using **bold** text.\n"
#             "- Use _italics_ for emphasis when necessary.\n"
#             "- For explanations, use bullet points or numbered lists to organize content:\n"
#             "  - Use `-` or `*` for bullet points.\n"
#             "  - Use `1.`, `2.`, `3.` for numbered lists.\n"
#             "- Provide examples where relevant to enhance understanding.\n"
#             "- Include links or references for further learning in Markdown format, such as:\n"
#             "  `[Click here](https://example.com)`.\n"
#             "- Use Markdown headers (e.g., `#`, `##`, `###`) for headings to structure the content.\n"
#             "- Avoid overly complex language; aim for simplicity and readability.\n"
#             "- Ensure the content is well-structured and engaging for students by leveraging Markdown's formatting capabilities."
#         )
#     }
#     user_message = {
#         "role": "user",
#         "content": (
#             f"Class: {input.class_name}, Subject: {input.subject_name}, "
#             f"Chapter: {input.chapter_name}, Topic: {input.topic_name}. Question: {input.question}"
#             "Provide your response in an educational tone with proper Markdown formatting. Use examples, diagrams (if applicable), and structured content for clarity. "
#             "Ensure the response is well-structured and includes headings, paragraphs, and lists where appropriate. "
#             "Suggest related questions for further exploration in bullet points."
#         )
#     }


#     # Combine incoming chat history with the new messages
#     messages = input.chat_history + [system_message, user_message]

#     try:
#         # Call OpenAI API for structured completion
#         completion = openai_client.beta.chat.completions.parse(
#             model="gpt-4o",  # Replace with your actual model
#             messages=messages,
#             response_format=ChatStructuredResponse,
#         )

#         structured_data = completion.choices[0].message.parsed
#         usage_data = completion.usage

#         # Extract token usage
#         input_tokens = getattr(usage_data, 'input_tokens', None)
#         output_tokens = getattr(usage_data, 'output_tokens', None)

#         # Append the new interaction to the chat history
#         updated_chat_history = input.chat_history + [
#             {"role": "user", "content": input.question},
#             {"role": "assistant", "content": structured_data.answer}
#         ]

#         # Save chat interaction in the database
#         chat_entry = ChatModel(
#             session_id=input.session_id,
#             request_message=user_message["content"],
#             response_message=structured_data.answer,
#             status="active",
#             input_tokens=input_tokens,
#             output_tokens=output_tokens,
#             model_used="gpt-4o",  # Update model name as needed
#             timestamp=datetime.utcnow()
#         )
#         db.add(chat_entry)
#         db.commit()
#         # Update session details
#         session.title = f"{input.class_name} - {input.subject_name} - {input.chapter_name} - {input.topic_name}"
#         session.last_message = structured_data.answer  # Save the AI's answer here
#         session.last_message_time = datetime.utcnow()
#         db.commit()
#         db.refresh(session)

#         # Return structured response with updated chat history
#         return create_response(
#             success=True,
#             message="Question processed successfully.",
#             data={
#                 "answer": structured_data.answer,
#                 "suggested_questions": structured_data.suggested_questions,
#                 "chat_history": updated_chat_history
#             },
#             status_code=200
#         )

#     except Exception as e:
#         logger.error(f"Error processing question: {str(e)}")
#         return create_response(success=False, message=f"OpenAI API error: {str(e)}", data=None, status_code=500)


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

# @router.get("/sessions", response_model=None)
# def get_sessions(
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     """
#     Retrieves a list of sessions for the current user.
#     """
#     try:
#         user_id = current_user.user_id

#         # Query sessions for the current user
#         sessions = db.query(SessionModel).filter(
#             SessionModel.user_id == user_id
#         ).order_by(SessionModel.started_at.desc()).all()

#         # Map sessions to response model
#         session_list = [
#             {
#                 "session_id": str(session.id),
#                 "title": session.title or "Untitled Session",
#                 "status": session.status,
#                 "last_message": session.last_message,
#                 "last_message_time": session.last_message_time.isoformat() if session.last_message_time else None,
#                 "started_at": session.started_at.isoformat(),
#                 "ended_at": session.ended_at.isoformat() if session.ended_at else None,
#             }
#             for session in sessions
#         ]

#         return create_response(success=True, message="Session list retrieved successfully", data=session_list)

#     except Exception as e:
#         logger.error(f"Error retrieving sessions: {str(e)}")
#         return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

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

        # Delete 'last_message is none Session' records

        # db.query(SessionModel).filter(
        #     SessionModel.user_id == user_id,
        #     (SessionModel.last_message == None)
        # ).delete(synchronize_session=False)
        # db.commit()

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

        response_data = []
        class_name, subject_name, chapter_name, topic_name = None, None, None, None

        for chat in chats:
            match = re.search(r"Class:\s*([^,]+),\s*Subject:\s*([^,]+),\s*Chapter:\s*([^,]+),\s*Topic:\s*([^\.]+)", chat.request_message)
            if match:
                class_name, subject_name, chapter_name, topic_name = match.groups()

            # Extract only the question part
            question_match = re.search(r"Question:\s*(.*?)(?:\s*Provide|\s*$)", chat.request_message, re.IGNORECASE)
            question = question_match.group(1).strip() if question_match else chat.request_message

            response_data.append(
                {"role": "user", "content": question}
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
            "topic_name": topic_name,
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
from typing import List

class AnalyzeImageInput(BaseModel):
    session_id: str  # Ensure session tracking
    image_urls: List[AnyHttpUrl]

@router.post("/analyze-image/")
def analyze_image_endpoint(
    images_input: AnalyzeImageInput,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("Received an image analysis request")

    # Validate and convert session_id to UUID
    try:
        session_id = uuid.UUID(images_input.session_id)
    except ValueError:
        logger.error(f"Invalid session_id format: {images_input.session_id}")
        return create_response(success=False, message="Invalid session ID format.", data=None, status_code=400)

    # Validate session_id
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id, SessionModel.status == "active"
    ).first()

    if not session:
        logger.error(f"Invalid or inactive session_id: {images_input.session_id}")
        return create_response(success=False, message="Invalid or inactive session ID.", data=None, status_code=400)

    # Ensure image URLs have valid formats
    for image_url in images_input.image_urls:
        image_url = str(image_url)  # Convert AnyHttpUrl to string
        if not image_url.lower().endswith((".png", ".jpeg", ".jpg", ".gif", ".webp")):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format for URL: {image_url}. Supported formats: png, jpeg, jpg, gif, webp.",
            )

    # Construct system and user messages
    system_message = {
        "role": "system",
        "content": (
            "You are an AI-powered image analysis assistant. "
            "Analyze the provided images and generate insightful descriptions. "
            "Ensure responses are clear, concise, and well-structured. "
            "Use bullet points or numbered lists for clarity where applicable."
        )
    }

    user_message = {
        "role": "user",
        "content": [{"type": "text", "text": "Describe the content of these images."}]
    }

    # Convert AnyHttpUrl to string before adding to messages
    for image_url in images_input.image_urls:
        user_message["content"].append({"type": "image_url", "image_url": {"url": str(image_url)}})

    # Combine chat history with new messages
    messages = [system_message, user_message]

    try:
        # Call OpenAI API for image analysis
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
        )

        analysis_result = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens

        # Generate insightful questions based on analysis
        question_prompt = f"Based on the provided images, generate 4 insightful questions that encourage further discussion.\n{analysis_result}"

        question_messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that analyzes images and provides meaningful insights."
            },
            {
                "role": "user",
                "content": question_prompt
            }
        ]

        question_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=question_messages,
            max_tokens=200,
        )

        generated_questions = question_response.choices[0].message.content.strip()

        # Append to chat history
        updated_chat_history = [
            user_message,
            {"role": "assistant", "content": analysis_result},
            {"role": "assistant", "content": f"Generated Questions:\n{generated_questions}"}
        ]

        # Save chat interaction in the database
        chat_entry = ChatModel(
            session_id=session_id,
            request_message="Image Analysis",
            response_message=analysis_result,
            status="active",
            input_tokens=tokens_used,
            output_tokens=None,  # Optional if not available
            model_used="gpt-4o-mini",
            timestamp=datetime.utcnow()
        )
        db.add(chat_entry)

        # Update session details
        session.last_message = analysis_result
        session.last_message_time = datetime.utcnow()

        db.commit()
        db.refresh(session)

        # Return structured response with updated chat history
        return create_response(
            success=True,
            message="Image analysis completed successfully.",
            data={
                "analysis_result": analysis_result,
                "generated_questions": generated_questions,
                "chat_history": updated_chat_history
            },
            status_code=200
        )

    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return create_response(success=False, message="AI processing error.", data=None, status_code=500)
    except Exception as e:
        logger.exception("Unexpected error occurred.")
        return create_response(success=False, message="An internal server error occurred.", data=None, status_code=500)
