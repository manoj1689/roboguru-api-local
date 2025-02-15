# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database import get_db
# from services.auth import get_current_user
# from models import SessionModel, ChatModel, User
# from schemas import QuestionInput, SessionCreateResponse, ChatStructuredResponse
# import openai
# import os
# import uuid
# from datetime import datetime
# from services.classes import create_response
# import logging

# # Load environment variables
# openai.api_key = os.getenv("OPENAI_API_KEY")
# if not openai.api_key:
#     raise ValueError("Missing OpenAI API key. Ensure it's set in the .env file.")

# # Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# router = APIRouter()

# MODEL = "gpt-4o"

# @router.post("/sessions/start", response_model=SessionCreateResponse)
# async def start_session(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     session_id = str(uuid.uuid4())
#     new_session = SessionModel(
#         id=session_id,
#         user_id=current_user.user_id,
#         status="active",
#         started_at=datetime.utcnow()
#     )
#     db.add(new_session)
#     db.commit()
#     db.refresh(new_session)

#     return create_response(
#         success=True,
#         message="New session started successfully.",
#         data={
#             "session_id": str(new_session.id),
#             "status": new_session.status,
#             "started_at": new_session.started_at.isoformat()
#         }
#     )

# @router.post("/ask-question/")
# def ask_question(
#     input: QuestionInput,
#     db: Session = Depends(get_db),
#     current_user: str = Depends(get_current_user)
# ):
#     try:
#         session_id = uuid.UUID(input.session_id)
#     except ValueError:
#         return create_response(success=False, message="Invalid session ID format.", data=None, status_code=400)

#     session = db.query(SessionModel).filter(
#         SessionModel.id == input.session_id, SessionModel.status == "active"
#     ).with_for_update().first()

#     if not session:
#         return create_response(success=False, message="Invalid or inactive session ID.", data=None, status_code=400)

#     chat_summary = input.chat_summary or session.chat_summary or ""

#     system_message = {
#         "role": "system",
#         "content": (
#             "You are an AI-powered educational assistant designed to help students learn effectively. "
#             "Use the following guidelines:\n"
#             "- Highlight important terms using **bold** text.\n"
#             "- Use _italics_ for emphasis when necessary.\n"
#             "- For explanations, use bullet points or numbered lists to organize content.\n"
#             "- Provide examples where relevant to enhance understanding.\n"
#             "- Include links or references for further learning in Markdown format.\n"
#             "- Use Markdown headers for headings to structure the content.\n"
#             "- Avoid overly complex language; aim for simplicity and readability.\n"
#             "- Ensure responses are engaging and well-structured by leveraging Markdown formatting.\n"
#             "- Maintain an educational tone, using structured content, examples, and diagrams where applicable.\n"
#             "- Responses should include headings, paragraphs, and lists where appropriate.\n"
#             "- Suggest related questions for further exploration using bullet points.\n"
#             "- Answer the question and **update the chat summary** by integrating the response into the conversation history.\n"
#             "- The chat summary should **evolve dynamically** based on previous interactions, the user's current question, and the AI-generated response."
#             "- If the user asks irrelevant, non-educational, or off-topic questions, provide a polite, simple response."
#         )
#     }

#     user_message = {
#         "role": "user",
#         "content": (
#             f"Class: {input.class_name}, Subject: {input.subject_name}, "
#             f"Chapter: {input.chapter_name}, Topic: {input.topic_name}.\n\n"
#             f"Question: {input.question}\n\n"
#             f"Previous Chat Summary:\n{chat_summary if chat_summary else 'None'}"
#         )
#     }

#     update_summary_prompt = {
#         "role": "assistant",
#         "content": (
#             "Based on the previous chat summary and the new question, generate an updated chat summary "
#             "that retains relevant past information, incorporates the AI response, and ensures the conversation context is maintained."
#         )
#     }

#     messages = [system_message, user_message, update_summary_prompt]

#     try:
#         completion = openai.ChatCompletion.create(
#             model=MODEL,
#             messages=messages,
#             response_format=ChatStructuredResponse,
#         )

#         if not completion.choices:
#             return create_response(success=False, message="No response received from OpenAI.", data=None, status_code=500)

#         structured_data = completion.choices[0].message.parsed
#         usage_data = completion.usage

#         input_tokens = getattr(usage_data, "input_tokens", 0)
#         output_tokens = getattr(usage_data, "output_tokens", 0)

#         suggested_questions = getattr(structured_data, "suggested_questions", [])

#         new_chat_summary = structured_data.chat_summary or chat_summary

#         chat_entry = ChatModel(
#             session_id=input.session_id,
#             request_message=input.question,
#             response_message=structured_data.answer,
#             status="active",
#             input_tokens=input_tokens,
#             output_tokens=output_tokens,
#             model_used=MODEL,
#             timestamp=datetime.utcnow()
#         )
#         db.add(chat_entry)
#         db.commit()
#         db.refresh(chat_entry)

#         session.last_message = structured_data.answer
#         session.last_message_time = datetime.utcnow()
#         session.title = f"{input.class_name} - {input.subject_name} - {input.chapter_name} - {input.topic_name}"
#         session.chat_summary = new_chat_summary
#         db.commit()
#         db.refresh(session)

#         return create_response(
#             success=True,
#             message="Question processed successfully.",
#             data={
#                 "answer": structured_data.answer,
#                 "suggested_questions": suggested_questions,
#                 "chat_summary": new_chat_summary
#             },
#             status_code=200
#         )

#     except Exception as e:
#         logger.error(f"OpenAI API Error: {str(e)}")
#         return create_response(success=False, message=f"OpenAI API error: {str(e)}", data=None, status_code=500)

# @router.get("/sessions", response_model=None)
# def get_sessions(
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     try:
#         user_id = current_user.user_id

#         sessions = db.query(SessionModel).filter(
#             SessionModel.user_id == user_id,
#             SessionModel.last_message != None
#         ).order_by(SessionModel.started_at.desc()).all()

#         session_list = []
#         for session in sessions:
#             title = session.title or "Unknown"
#             title_parts = title.split(" - ")

#             class_name = title_parts[0] if len(title_parts) > 0 else "Unknown"
#             subject_name = title_parts[1] if len(title_parts) > 1 else "Unknown"
#             chapter_name = title_parts[2] if len(title_parts) > 2 else "Unknown"
#             topic = title_parts[3] if len(title_parts) > 3 else title
#             session_list.append({
#                 "session_id": str(session.id),
#                 "class_name": class_name,
#                 "subject_name": subject_name,
#                 "chapter_name": chapter_name,
#                 "topic": topic,
#                 "title": topic,
#                 "status": session.status,
#                 "last_message": session.last_message,
#                 "last_message_time": session.last_message_time.isoformat() if session.last_message_time else None,
#                 "started_at": session.started_at,
#                 "ended_at": session.ended_at.isoformat() if session.ended_at else None,
#             })
#         session_list.sort(key=lambda x: (x["title"] == "Unknown", -x["started_at"].timestamp()))

#         for session in session_list:
#             session["started_at"] = session["started_at"].isoformat()
#         return create_response(success=True, message="Session list retrieved successfully", data=session_list)

#     except Exception as e:
#         logger.error(f"Error retrieving sessions: {str(e)}")
#         return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

# @router.delete("/sessions/{session_id}")
# def delete_session(
#     session_id: uuid.UUID,
#     db: Session = Depends(get_db),
#     current_user: str = Depends(get_current_user)
# ):
#     try:
#         session = db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.status == "active").first()
#         if not session:
#             return create_response(success=False, message="Session not found or already deleted")
#         session.status = "deleted"
#         db.commit()
#         return create_response(success=True, message="Session deleted successfully")
#     except Exception as e:
#         return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

# @router.get("/sessions/{session_id}/chats", response_model=dict)
# def get_chats_for_session(
#     session_id: uuid.UUID,
#     db: Session = Depends(get_db),
#     current_user: str = Depends(get_current_user)
# ):
#     try:
#         chats = db.query(ChatModel).filter(
#             ChatModel.session_id == session_id,
#             ChatModel.status == "active"
#         ).order_by(ChatModel.timestamp).all()
#         if not chats:
#             return create_response(success=False, message="No chats found for this session")

#         session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

#         title = session.title or "Unknown"
#         title_parts = title.split(" - ")

#         class_name = title_parts[0] if len(title_parts) > 0 else "Unknown"
#         subject_name = title_parts[1] if len(title_parts) > 1 else "Unknown"
#         chapter_name = title_parts[2] if len(title_parts) > 2 else "Unknown"
#         topic = title_parts[3] if len(title_parts) > 3 else title

#         response_data = []

#         for chat in chats:
#             response_data.append(
#                 {"role": "user", "content": chat.request_message}
#             )
#             response_data.append(
#                 {"role": "assistant", "content": chat.response_message}
#             )

#         return {
#             "success": True,
#             "message": "Chats found for this session successfully",
#             "session_id": str(session_id),
#             "class_name": class_name,
#             "subject_name": subject_name,
#             "chapter_name": chapter_name,
#             "topic_name": topic,
#             "data": response_data
#         }

#     except Exception as e:
#         return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

# @router.delete("/chats/{chat_id}")
# def delete_chat(
#     chat_id: uuid.UUID,
#     db: Session = Depends(get_db),
#     current_user: str = Depends(get_current_user)
# ):
#     try:
#         chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.status == "active").first()
#         if not chat:
#             return create_response(success=False, message="Chat not found or already deleted")
#         chat.status = "deleted"
#         db.commit()
#         return create_response(success=True, message="Chat deleted successfully")
#     except Exception as e:
#         return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.auth import get_current_user
from models import SessionModel, ChatModel, User
from schemas import QuestionInput, SessionCreateResponse, ChatStructuredResponse
import openai
import os
import uuid
from datetime import datetime
from services.classes import create_response
import logging
from services.chat import construct_prompt  # New import for prompt construction

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Missing OpenAI API key. Ensure it's set in the .env file.")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

MODEL = "gpt-4o"

@router.post("/sessions/start", response_model=SessionCreateResponse)
async def start_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = str(uuid.uuid4())
    new_session = SessionModel(
        id=session_id,
        user_id=current_user.user_id,
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

    messages = construct_prompt(input, session)

    try:
        completion = openai.ChatCompletion.create(
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

        new_chat_summary = structured_data.chat_summary or session.chat_summary

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
        return create_response(success=True, message="Session deleted successfully")
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
        ).order_by(ChatModel.timestamp).all()
        if not chats:
            return create_response(success=False, message="No chats found for this session")

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
        return create_response(success=True, message="Chat deleted successfully")
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")