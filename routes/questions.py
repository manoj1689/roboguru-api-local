from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Exam
from database import get_db
from services.auth import get_current_user
import json
from services.classes import create_response
from services.questions import generate_questions
from schemas import QuestionRequest, MixedQuestionRequest, AnswerRequest
from datetime import datetime
import uuid
from services.questions import evaluate_answers

router = APIRouter()

@router.post("/objective")
async def get_objective_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("objective", request.dict())
        
        # Check if the response is valid
        if not isinstance(response, dict):
            return create_response(success=False, message= "Invalid response format from OpenAI", data=None)

        # Extract questions
        questions_with_answers = response.get('questions', [])
        
        if not questions_with_answers:
            return create_response(success=True, message= "No valid questions generated.", data=None)

        # Continue with exam creation...
        exam_id = str(uuid.uuid4())
        
        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),
            class_name=request.class_name,             
            subject_name=request.subject_name,      
            chapter_name=request.chapter_name,       
            topic_name=request.topic_name,               
            exam_title=f"{request.topic_name or 'General'} Objective Quiz",
            exam_description="An objective quiz.",
            questions_with_answers=json.dumps(questions_with_answers),
            status="draft",
            created_at=datetime.utcnow(),
        )
        # print(f"Exam data: {exam.to_dict()}") 
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="Objective questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),
                "exam_title": str(exam.exam_title),
                "class_name": str(exam.class_name),
                "subject_name": str(exam.subject_name),
                "chapter_name": str(exam.chapter_name),
                "topic_name": str(exam.topic_name),
                "questions": questions_with_answers,
            },
        )

    except Exception as e:
        db.rollback()
        print(f"Error while saving exam: {str(e)}")
        return create_response(success=False, message=f"Error generating questions: {str(e)}")

@router.post("/true_false")
async def get_true_false_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("true_false", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            return create_response(success=True, message= "No valid questions generated.", data=None)

        exam_id = str(uuid.uuid4())  # Convert UUID to string

        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),  # Convert UUID to string
            class_name=request.class_name,             
            subject_name=request.subject_name,      
            chapter_name=request.chapter_name,       
            topic_name=request.topic_name,   
            exam_title=f"{request.topic_name or 'General'} True/False Quiz",
            exam_description="A true/false quiz.",
            questions_with_answers=questions_with_answers,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="True/False questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),  # Convert UUID to string
                "exam_title": str(exam.exam_title),
                "class_name": str(exam.class_name),
                "subject_name": str(exam.subject_name),
                "chapter_name": str(exam.chapter_name),
                "topic_name": str(exam.topic_name),             
                "questions": questions_with_answers,
            },
        )

    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error generating questions: {str(e)}")



@router.post("/fill_in_blank")
async def get_fill_in_blank_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("fill_in_blank", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            return create_response(success=True, message= "No valid questions generated.", data=None)
        
        exam_id = str(uuid.uuid4())  # Convert UUID to string

        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),  # Convert UUID to string
            class_name=request.class_name,             
            subject_name=request.subject_name,      
            chapter_name=request.chapter_name,       
            topic_name=request.topic_name,    
            exam_title=f"{request.topic_name or 'General'} Fill-in-the-Blank Quiz",
            exam_description="A fill-in-the-blank quiz.",
            questions_with_answers=questions_with_answers,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="Fill-in-the-blank questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),  # Convert UUID to string
                "exam_title": str(exam.exam_title),
                "class_name": str(exam.class_name),
                "subject_name": str(exam.subject_name),
                "chapter_name": str(exam.chapter_name),
                "topic_name": str(exam.topic_name),
                "questions": questions_with_answers,
            },
        )

    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error generating questions: {str(e)}")



@router.post("/descriptive")
async def get_descriptive_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("descriptive", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            return create_response(success=True, message= "No valid questions generated.", data=None)

        exam_id = str(uuid.uuid4())  # Convert UUID to string

        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),  # Convert UUID to string
            class_name=request.class_name,             
            subject_name=request.subject_name,      
            chapter_name=request.chapter_name,       
            topic_name=request.topic_name,    
            exam_title=f"{request.topic_name or 'General'} Descriptive Quiz",
            exam_description="A descriptive quiz.",
            questions_with_answers=questions_with_answers,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="Descriptive questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),  # Convert UUID to string
                "class_name": str(exam.class_name),
                "subject_name": str(exam.subject_name),
                "chapter_name": str(exam.chapter_name),
                "topic_name": str(exam.topic_name),
                "questions": questions_with_answers,
            },
        )

    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error generating questions: {str(e)}")



@router.post("/mixed")
async def get_mixed_questions(request: MixedQuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("mixed", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            return create_response(success=True, message= "No valid questions generated.", data=None)

        exam_id = str(uuid.uuid4())  

        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),  # Convert UUID to string
            class_name=request.class_name,             
            subject_name=request.subject_name,      
            chapter_name=request.chapter_name,       
            topic_name=request.topic_name,   
            exam_title=f"{request.topic_name or 'General'} Mixed Quiz",
            exam_description="A mixed quiz.",
            questions_with_answers=questions_with_answers,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="Mixed questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),  # Convert UUID to string
                "exam_title": str(exam.exam_title),
                "class_name": str(exam.class_name),
                "subject_name": str(exam.subject_name),
                "chapter_name": str(exam.chapter_name),
                "topic_name": str(exam.topic_name),
                "questions": questions_with_answers,
            },
        )

    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error generating questions: {str(e)}")

@router.post("/evaluate_exam")
async def evaluate_exam(request: AnswerRequest, db: Session = Depends(get_db)):
    try:
        # Fetch Exam Data
        exam = db.query(Exam).filter(Exam.id == request.exam_id).first()

        if not exam:
            return create_response(success=False, message="Exam not found")

        # Convert question structure into AI-parsable format
        questions_with_answers = []
        total_marks = request.max_marks
        obtained_marks = 0
        questions_feedback = [] 

        for q in request.questions:
            question_data = {
                "id": q["id"],
                "question": q["text"],
                "marks": q["marks"]
            }

            # total_marks += q["marks"]

            if q["type"] == "objective":
                question_data["options"] = q["options"]
                question_data["correct_answer"] = q["options"][q["correct_answer"]["option_index"]]
                question_data["student_answer"] = q["options"][q["student_answer"]]

            elif q["type"] == "true_false":
                question_data["correct_answer"] = q["correct_answer"]["value"]
                question_data["student_answer"] = q["student_answer"]

            elif q["type"] == "fill_in_blank":
                if isinstance(q["correct_answer"]["answers"], list):
                    correct_answers = q["correct_answer"]["answers"]
                else:
                    correct_answers = [q["correct_answer"]["answers"]]  
                
            elif q["type"] == "descriptive":
                question_data["correct_answer"] = q["correct_answer"]["criteria"]
                question_data["student_answer"] = q["student_answer"]

            questions_with_answers.append(question_data)
        print("Formatted Questions Sent to AI:", json.dumps(questions_with_answers, indent=2))

        evaluation_result = await evaluate_answers(questions_with_answers)
        print("Evaluation Result from AI:", evaluation_result)

        # Ensure AI response contains expected data
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

        # Save evaluation result in database
        exam.score = obtained_marks
        exam.remark = overall_feedback
        exam.status = "evaluating_result"
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="Exam evaluated successfully.",
            data={
                "exam_id": request.exam_id,
                "total_marks": total_marks,
                "obtained_marks": obtained_marks,
                "questions_feedback": questions_feedback,
                "overall_feedback": overall_feedback
            },
        )

    except Exception as e:
        db.rollback()
        return create_response(success=False, message=f"Error evaluating exam: {str(e)}")
