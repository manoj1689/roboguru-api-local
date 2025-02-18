from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging
from utils.response import create_response
from models.user import User
from models.session import SessionModel
from models.chat import ChatModel
from utils.openai_client import get_ai_response
from schemas import QuestionInput
from utils.openai_client import MODEL


logger = logging.getLogger(__name__)

def validate_session_id(session_id: str):
    """Validate if session ID is a valid UUID."""
    try:
        return uuid.UUID(session_id)
    except ValueError:
        return None

def fetch_active_session(db: Session, session_id: str):
    """Fetch an active session from the database."""
    return (
        db.query(SessionModel)
        .filter(SessionModel.id == session_id, SessionModel.status == "active")
        .with_for_update()
        .first()
    )

def prepare_messages(input: QuestionInput, chat_summary: str):
    """Prepare system, user, and AI prompt messages."""
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

    update_summary_prompt = {
        "role": "assistant",
        "content": (
            "Based on the previous chat summary and the new question, generate an updated chat summary "
            "that retains relevant past information, incorporates the AI response, and ensures the conversation context is maintained."
        )
    }

    return [system_message, user_message, update_summary_prompt]

def save_chat_entry(db: Session, session_id: str, input_question: str, structured_data, input_tokens: int, output_tokens: int):
    """Save the chat response to the database."""
    chat_entry = ChatModel(
        session_id=session_id,
        request_message=input_question,
        response_message=structured_data.answer,
        status="active",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model_used=MODEL,
        timestamp=datetime.utcnow(),
    )
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)
    return chat_entry

def update_session_metadata(db: Session, session, structured_data, input):
    """Update the session metadata after a new chat entry."""
    session.last_message = structured_data.answer
    session.last_message_time = datetime.utcnow()
    session.title = f"{input.class_name} - {input.subject_name} - {input.chapter_name} - {input.topic_name}"
    session.chat_summary = structured_data.chat_summary if structured_data.chat_summary else session.chat_summary
    db.commit()
    db.refresh(session)

def process_question(input: QuestionInput, db: Session, current_user: str):
    """Main function to process the user's question."""
    session_id = validate_session_id(input.session_id)
    if not session_id:
        return create_response(False, "Invalid session ID format.", None, 400)

    session = fetch_active_session(db, input.session_id)
    if not session:
        return create_response(False, "Invalid or inactive session ID.", None, 400)

    chat_summary = input.chat_summary if input.chat_summary else session.chat_summary or ""

    messages = prepare_messages(input, chat_summary)

    try:
        structured_data, input_tokens, output_tokens = get_ai_response(messages)

        if not structured_data:
            return create_response(False, "No response received from OpenAI.", None, 500)

        chat_entry = save_chat_entry(db, input.session_id, input.question, structured_data, input_tokens, output_tokens)

        update_session_metadata(db, session, structured_data, input)

        return create_response(
            True,
            "Question processed successfully.",
            {
                "answer": structured_data.answer,
                "suggested_questions": getattr(structured_data, "suggested_questions", []),
                "chat_summary": structured_data.chat_summary or chat_summary,
            },
            200,
        )

    except Exception as e:
        logger.error(f"OpenAI API Error: {str(e)}")
        return create_response(False, f"OpenAI API error: {str(e)}", None, 500)


def start_new_session(db: Session, current_user: User):
    """Start a new chat session"""
    try:
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
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        return create_response(success=False, message="Failed to start session")

def fetch_sessions(db: Session, current_user: User):
    """Retrieve user's chat sessions"""
    try:
        user_id = current_user.user_id

        if not user_id:
            logger.error("User ID is missing in the request")
            return create_response(success=False, message="User authentication failed")

        sessions = db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.last_message != None
        ).order_by(SessionModel.started_at.desc()).all()

        if not sessions:
            logger.info(f"No sessions found for user: {user_id}")
            return create_response(success=True, message="No sessions found", data=[])

        session_list = []
        for session in sessions:
            try:
                title_parts = session.title.split(" - ") if session.title else ["Unknown"]
                class_name = title_parts[0] if len(title_parts) > 0 else "Unknown"
                subject_name = title_parts[1] if len(title_parts) > 1 else "Unknown"
                chapter_name = title_parts[2] if len(title_parts) > 2 else "Unknown"
                topic = title_parts[3] if len(title_parts) > 3 else session.title

                session_list.append({
                    "session_id": str(session.id),
                    "class_name": class_name,
                    "subject_name": subject_name,
                    "chapter_name": chapter_name,
                    "topic": topic,
                    "title": session.title,
                    "status": session.status,
                    "last_message": session.last_message,
                    "last_message_time": session.last_message_time.isoformat() if session.last_message_time else None,
                    "started_at": session.started_at.isoformat(),
                    "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                })
            except Exception as inner_error:
                logger.error(f"Error processing session {session.id}: {str(inner_error)}")

        return create_response(success=True, message="Session list retrieved successfully", data=session_list)

    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}", data={})



def remove_session(db: Session, session_id: uuid.UUID):
    """Delete a specific chat session"""
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.status == "active").first()
        if not session:
            return create_response(success=False, message="Session not found or already deleted")
        
        session.status = "deleted"
        db.commit()
        return create_response(success=True, message="Session deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        return create_response(success=False, message="Failed to delete session")


def fetch_chats_for_session(db: Session, session_id: uuid.UUID):
    """Fetch all chat messages for a session"""
    try:
        chats = db.query(ChatModel).filter(
            ChatModel.session_id == session_id,
            ChatModel.status == "active"
        ).order_by(ChatModel.timestamp).all()

        if not chats:
            return create_response(success=False, message="No chats found for this session")

        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

        title_parts = session.title.split(" - ") if session.title else ["Unknown"]
        class_name, subject_name, chapter_name, topic = (
            title_parts + ["Unknown"] * (4 - len(title_parts))
        )[:4]

        response_data = [{"role": "user", "content": chat.request_message} for chat in chats] + \
                        [{"role": "assistant", "content": chat.response_message} for chat in chats]

        return create_response(
            success=True,
            message="Chats found for this session successfully",
            data={
                "session_id": str(session_id),
                "class_name": class_name,
                "subject_name": subject_name,
                "chapter_name": chapter_name,
                "topic_name": topic,
                "data": response_data
            }
        )

    except Exception as e:
        logger.error(f"Error fetching chats: {str(e)}")
        return create_response(success=False, message="Failed to retrieve chats")


def remove_chat(db: Session, chat_id: uuid.UUID):
    """Delete a chat message"""
    try:
        chat = db.query(ChatModel).filter(ChatModel.id == chat_id, ChatModel.status == "active").first()
        if not chat:
            return create_response(success=False, message="Chat not found or already deleted")
        
        chat.status = "deleted"
        db.commit()
        return create_response(success=True, message="Chat deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        return create_response(success=False, message="Failed to delete chat")
