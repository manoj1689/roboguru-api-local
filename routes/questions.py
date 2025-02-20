from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.exam import Exam
from database import get_db
from utils.auth import get_current_user
import json
from utils.response import create_response
from services.questions import generate_questions, evaluate_answers
from schemas.question import QuestionRequest, MixedQuestionRequest, AnswerRequest
from datetime import datetime
import uuid

router = APIRouter()

# async def create_exam(request, question_type, db: Session, current_user):
#     try:
#         # Unpacking the response correctly
#         response, input_tokens, output_tokens, total_tokens, gen_time = await generate_questions(question_type, request.dict())
        
#         questions_with_answers = response.get('questions', [])
#         if not questions_with_answers:
#             return create_response(success=True, message="No valid questions generated.", data=None)

#         exam_id = str(uuid.uuid4())
#         exam = Exam(
#             id=exam_id,
#             user_id=str(current_user.user_id),
#             class_name=request.class_name,
#             subject_name=request.subject_name,
#             chapter_name=request.chapter_name,
#             topic_name=request.topic_name,
#             exam_title=f"{request.topic_name or 'General'} {question_type.replace('_', ' ').title()} Quiz",
#             exam_description=f"A {question_type.replace('_', ' ')} quiz.",
#             questions_with_answers=json.dumps(questions_with_answers),  # Ensure JSON serialization
#             status="draft",
#             created_at=datetime.utcnow(),
#         )
#         db.add(exam)
#         db.commit()
#         db.refresh(exam)

#         return create_response(
#             success=True,
#             message=f"{question_type.replace('_', ' ').title()} questions generated and saved successfully.",
#             data={
#                 "exam_id": str(exam.id),
#                 "exam_title": str(exam.exam_title),
#                 "class_name": str(exam.class_name),
#                 "subject_name": str(exam.subject_name),
#                 "chapter_name": str(exam.chapter_name),
#                 "topic_name": str(exam.topic_name),
#                 "questions": questions_with_answers,
#                 "input_tokens": input_tokens,
#                 "output_tokens": output_tokens,
#                 "total_tokens": total_tokens,
#                 "generation_time": gen_time
#             },
#         )
#     except Exception as e:
#         db.rollback()
#         return create_response(success=False, message=f"Error generating questions: {str(e)}")

async def create_exam(request, question_type, db: Session, current_user):
    try:
        response, input_tokens, output_tokens, total_tokens, gen_time = await generate_questions(question_type, request.dict())

        questions_with_answers = response.get('questions', {})
        if not questions_with_answers:
            return create_response(success=True, message="No valid questions generated.", data=None)

        exam_id = str(uuid.uuid4())
        total_questions = sum(len(questions) for questions in questions_with_answers.values())
        total_marks = sum(sum(q['marks'] for q in questions) for questions in questions_with_answers.values())
        total_time = total_questions * 2  # Assuming each question takes 2 minutes on average

        # Convert ChapterTopic objects to dictionaries
        chapters_dict = [chapter.dict() for chapter in request.chapters]

        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),
            class_name=request.class_name,
            subject_name=request.subject_name,
            exam_title=f"{request.chapters[0].chapter_name if request.chapters else 'General'} {question_type.replace('_', ' ').title()} Quiz",
            exam_description=f"A {question_type.replace('_', ' ')} quiz.",
            questions_with_answers=json.dumps(questions_with_answers),
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message=f"{question_type.replace('_', ' ').title()} questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),
                "exam_title": exam.exam_title,
                "class_name": exam.class_name,
                "subject_name": exam.subject_name,
                "chapters": chapters_dict,  # Include the serialized chapters
                "total_questions": total_questions,
                "total_marks": total_marks,
                "total_time": total_time,
                "questions": questions_with_answers,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "generation_time": gen_time
            },
        )
    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error generating questions: {str(e)}")

@router.post("/objective")
async def get_objective_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await create_exam(request, "objective", db, current_user)

@router.post("/true_false")
async def get_true_false_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await create_exam(request, "true_false", db, current_user)

@router.post("/fill_in_blank")
async def get_fill_in_blank_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await create_exam(request, "fill_in_blank", db, current_user)

@router.post("/descriptive")
async def get_descriptive_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await create_exam(request, "descriptive", db, current_user)

@router.post("/mixed")
async def get_mixed_questions(request: MixedQuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await create_exam(request, "mixed", db, current_user)

# Endpoint to evaluate exam
@router.post("/evaluate_exam")
async def evaluate_exam(request: AnswerRequest, db: Session = Depends(get_db)):
    try:
        # Fetch the exam from the database
        exam = db.query(Exam).filter(Exam.id == request.exam_id).first()
        if not exam:
            return create_response(success=False, message="Exam not found")

        # Prepare questions with answers for evaluation
        questions_with_answers = []
        total_marks = request.max_marks
        obtained_marks = 0
        questions_feedback = []

        for q in request.questions:
            question_data = {
                "id": q.id,
                "question": q.text,
                "marks": q.marks,
                "student_answer": q.student_answer
            }

            if q.type == "objective" and q.options:
                question_data["options"] = q.options
                if q.correct_answer.option_index is not None:
                    question_data["correct_answer"] = q.options[q.correct_answer.option_index]

            elif q.type == "true_false":
                if q.correct_answer.value is not None:
                    question_data["correct_answer"] = q.correct_answer.value

            elif q.type == "fill_in_blank":
                if q.correct_answer.answers:
                    question_data["correct_answer"] = q.correct_answer.answers

            elif q.type == "descriptive":
                if q.correct_answer.criteria:
                    question_data["correct_answer"] = q.correct_answer.criteria

            questions_with_answers.append(question_data)

        # Evaluate the answers using the AI function
        evaluation_result = await evaluate_answers(questions_with_answers)

        if "questions" in evaluation_result:
            for result in evaluation_result["questions"]:
                obtained_marks += result.get("marks_obtained", 0)
                question_feedback = {
                    "id": result["id"],
                    "obtained_marks": result["marks_obtained"],
                    "status": result.get("status", "unknown"),
                    "feedback": result["feedback"]
                }
                questions_feedback.append(question_feedback)

        overall_feedback = evaluation_result.get("overall_feedback", "Good attempt! Keep practicing.")

        # Update the exam record in the database
        exam.score = obtained_marks
        exam.remark = overall_feedback
        exam.status = "evaluating_result"
        db.commit()
        db.refresh(exam)

        # Calculate additional metrics
        total_time_taken = (request.exam_end_time - request.exam_start_time).total_seconds() / 60  # in minutes
        total_questions = len(request.questions)
        total_correct_answers = sum(1 for feedback in questions_feedback if feedback["status"] == "correct")
        total_incorrect_answers = sum(1 for feedback in questions_feedback if feedback["status"] == "incorrect")
        total_unanswered_questions = total_questions - (total_correct_answers + total_incorrect_answers)
        accuracy = (total_correct_answers / total_questions) * 100 if total_questions > 0 else 0

        return create_response(
            success=True,
            message="Exam evaluated successfully.",
            data={
                "exam_id": request.exam_id,
                "total_marks": total_marks,
                "obtained_marks": obtained_marks,
                "total_time_taken": total_time_taken,
                "accuracy": accuracy,
                "total_correct_answers": total_correct_answers,
                "total_incorrect_answers": total_incorrect_answers,
                "total_unanswered_questions": total_unanswered_questions,
                "questions_feedback": questions_feedback,
                "overall_feedback": overall_feedback
            },
        )

    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error evaluating exam: {str(e)}")