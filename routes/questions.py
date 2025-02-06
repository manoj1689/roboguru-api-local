from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Exam
from database import get_db
from services.auth import get_current_user
import json
from services.classes import create_response
from services.questions import generate_questions
from schemas import QuestionRequest, MixedQuestionRequest
from datetime import datetime
import uuid

router = APIRouter()



@router.post("/objective")
async def get_objective_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        # Generate questions using OpenAI API
        response = await generate_questions("objective", request.dict())
        
        # Log the raw response to check its content
        print(response)  # For debugging, remove in production

        # Check if the response is valid
        if not isinstance(response, dict):
            raise ValueError("Invalid response format from OpenAI")

        # Extract questions
        questions_with_answers = response.get('questions', [])
        
        if not questions_with_answers:
            raise ValueError("No valid questions generated.")

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
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@router.post("/true_false")
async def get_true_false_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("true_false", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            raise ValueError("No valid questions generated.")

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
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/fill_in_blank")
async def get_fill_in_blank_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("fill_in_blank", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            raise ValueError("No valid questions generated.")

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
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/descriptive")
async def get_descriptive_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("descriptive", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            raise ValueError("No valid questions generated.")

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
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/mixed")
async def get_mixed_questions(request: MixedQuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions("mixed", request.dict())
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            raise ValueError("No valid questions generated.")

        exam_id = str(uuid.uuid4())  # Convert UUID to string

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
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
