from dotenv import load_dotenv
import logging
import os
import uuid
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OpenAI client with environment
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ========== Structured Model for "start exam" ========== #
class ExamStructuredResponse(BaseModel):
    """
    Distinct model for the Exam scenario:
    e.g., 'instructions', 'time_limit', 'questions', etc.
    """
    instructions: str
    time_limit: str
    questions: Optional[List[str]] = Field(default_factory=list)

class StartExamRequest(BaseModel):
    exam_id: str
    subject: str
    difficulty: Optional[str] = "medium"

class StartExamResponse(BaseModel):
    error: Optional[str] = None
    data: Optional[ExamStructuredResponse] = None

# ========== Structured Model for "evaluate answers" ========== #
class SingleAnswerFeedback(BaseModel):
    """
    Represents feedback for a single question’s answer:
    e.g. question_id, score (0-100), remarks or commentary
    """
    question_id: str
    score: int
    remarks: Optional[str]

class EvaluateAnswersRequest(BaseModel):
    """
    User provides exam_id, a list of question->answer pairs
    that we want OpenAI to evaluate or “grade”
    """
    exam_id: str
    subject: str
    answers: List[dict]  # each item: {"question_id": "Q1", "question": "...", "answer_text": "..."}

class EvaluateAnswersStructuredResponse(BaseModel):
    """
    The structured data we want from OpenAI:
    - overall_score: Summation or average of all answers
    - overall_feedback: text
    - details: list of SingleAnswerFeedback
    """
    overall_score: int
    overall_feedback: str
    details: List[SingleAnswerFeedback]

class EvaluateAnswersResponse(BaseModel):
    error: Optional[str] = None
    data: Optional[EvaluateAnswersStructuredResponse] = None

# ========== Model for images submission ========== #
class ImageUploadResponse(BaseModel):
    upload_status: str
    file_count: int
    file_paths: List[str]

# ========== EXAM ROUTES ========== #

@router.post("/start", response_model=StartExamResponse)
def start_exam(request: StartExamRequest):
    """
    Simulate starting an exam by calling OpenAI
    with a separate structured parse model: ExamStructuredResponse.
    """
    logger.info("Starting exam: exam_id=%s, subject=%s, difficulty=%s",
                request.exam_id, request.subject, request.difficulty)

    system_message = {
        "role": "system",
        "content": (
            "You are an AI generating exam details in JSON. Fields: 'instructions', "
            "'time_limit', 'questions'. Provide a realistic exam scenario."
        )
    }
    user_message = {
        "role": "user",
        "content": (
            f"Exam: {request.exam_id}, Subject: {request.subject}, Difficulty: {request.difficulty}. "
            "Generate instructions, time limit, and a question set."
        )
    }
    messages = [system_message, user_message]

    try:
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=ExamStructuredResponse,
        )
        structured_data = completion.choices[0].message.parsed
        return StartExamResponse(error=None, data=structured_data)

    except Exception as e:
        logger.error("Error in start_exam: %s", e)
        return StartExamResponse(error=str(e), data=None)


@router.post("/submit-images", response_model=ImageUploadResponse)
async def submit_exam_images(files: List[UploadFile] = File(...)):
    """
    Accepts multiple images as final exam submissions.
    Saves them locally in 'uploaded_images/'.
    """
    logger.info("Submitting %d images for exam results", len(files))
    upload_dir = "uploaded_images"
    file_paths = []

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        destination = os.path.join(upload_dir, unique_name)
        try:
            with open(destination, "wb") as f:
                f.write(await file.read())
            file_paths.append(destination)
        except Exception as e:
            logger.error("Failed to save file %s: %s", unique_name, e)
            raise HTTPException(status_code=500, detail=f"Could not upload {file.filename}")

    return ImageUploadResponse(
        upload_status="Images uploaded successfully.",
        file_count=len(files),
        file_paths=file_paths
    )


@router.post("/evaluate", response_model=EvaluateAnswersResponse)
def evaluate_answers(request: EvaluateAnswersRequest):
    """
    Receives user answers and calls OpenAI
    to produce a structured parse with overall + per-answer feedback.
    """
    logger.info("Evaluating answers for exam_id=%s, subject=%s, count=%d",
                request.exam_id, request.subject, len(request.answers))

    # Build system & user messages
    system_message = {
        "role": "system",
        "content": (
            "You are an AI exam grader. You will receive a list of question->answer pairs. "
            "Generate a JSON object with fields: 'overall_score' (0-100, average?), "
            "'overall_feedback' (string), and 'details' (array of question feedback). "
            "Each item in 'details' must have 'question_id', 'score', 'remarks'."
        )
    }

    # user_message content includes all answers as text
    # e.g. "Exam: EXM101, Subject: Biology. Questions: Q1->..., Answer->..."
    lines = [
        f"Exam: {request.exam_id}, Subject: {request.subject}",
        "Evaluate these answers and provide JSON feedback."
    ]
    for ans in request.answers:
        q_id = ans.get("question_id", "???")
        q_text = ans.get("question", "")
        a_text = ans.get("answer_text", "")
        lines.append(f"Question ID: {q_id}, Q: {q_text} | User Answer: {a_text}")

    user_message = {
        "role": "user",
        "content": "\n".join(lines)
    }

    messages = [system_message, user_message]

    try:
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=EvaluateAnswersStructuredResponse,
        )
        structured_data = completion.choices[0].message.parsed
        # structured_data is an instance of EvaluateAnswersStructuredResponse

        return EvaluateAnswersResponse(error=None, data=structured_data)

    except Exception as e:
        logger.error("Error in evaluate_answers: %s", e)
        return EvaluateAnswersResponse(error=str(e), data=None)
