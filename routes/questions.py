# from fastapi import APIRouter, HTTPException, Depends
# from sqlalchemy.orm import Session
# from models import Exam
# from database import get_db
# from services.auth import get_current_user
# from pydantic import BaseModel
# from typing import Optional, Dict
# import openai
# import os
# import json
# from dotenv import load_dotenv
# import os
# from services.classes import create_response
# from datetime import datetime
# import uuid

# load_dotenv()
# # Define the router
# router = APIRouter()

# # Define request models
# class QuestionRequest(BaseModel):
#     class_name: str
#     subject_name: str
#     chapter_name: Optional[str] = None  
#     topic_name: Optional[str] = None 
#     num_questions: int = 5
#     difficulty: str = "medium"

# class MixedQuestionRequest(QuestionRequest):
#     question_distribution: Dict[str, int]

# # Set the API key
# openai.api_key = os.getenv("OPENAI_API_KEY")
# if not openai.api_key:
#     raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# async def generate_questions(question_type: str, payload: dict):
#     """Handles API calls for different question types."""
#     messages = [
#         {
#             "role": "system",
#             "content": "You are an educational assistant that generates quiz questions in valid JSON format."
#         }
#     ]

#     question_prompts = {
#         "objective": f"Generate exactly {payload['num_questions']} objective (multiple-choice) questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Objective Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'objective', 'text': 'Your question here.', 'options': ['Option1', 'Option2', 'Option3', 'Option4'], 'marks': 2, 'correct_answer': {{'option_index': correct_option_index}} }}]}}.",        
#         "true_false": f"Generate exactly {payload['num_questions']} true/false questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} True/False Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'true_false', 'text': 'Your question here.', 'marks': 1, 'correct_answer': true/false }}]}}.",    
#         "fill_in_blank": f"Generate exactly {payload['num_questions']} fill-in-the-blank questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Fill-in-the-blank Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'fill_in_blank', 'text': 'Your question here with ____', 'marks': 2, 'correct_answer': {{'answers': ['Correct Answer']}} }}]}}.",        
#         "descriptive": f"Generate exactly {payload['num_questions']} descriptive questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Descriptive Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'descriptive', 'text': 'Your question here.', 'marks': 5, 'correct_answer': {{'criteria': 'Expected key points'}} }}]}}.",        
#         "mixed": f"Generate a mixed exam for Class {payload['class_name']} on the subject_name '{payload['subject_name']}', chapter_name '{payload['chapter_name']}', and topic_name '{payload.get('topic_name', 'general')}' with the following distribution: {payload.get('question_distribution', {})}. Include objective, true/false, fill-in-the-blank, and descriptive questions as specified. Return the response in JSON format with the structure: {{'exam_title': '{payload.get('topic_name', 'General')} Mixed Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'question_type', 'text': 'Your question here.', 'marks': question_marks, 'correct_answer': {{'answer_key': 'expected value based on type'}} }}]}}."
#     }

#     if question_type not in question_prompts:
#         raise ValueError(f"Unsupported question type: {question_type}")

#     messages.append({"role": "user", "content": question_prompts[question_type]})

#     try:
#         # Call the OpenAI API for chat completions
#         response = openai.chat.completions.create(
#             model="gpt-4", 
#             messages=messages,
#             temperature=0,
#             max_tokens=2000
#         )

#         # Extract the generated content and validate as JSON
#         # generated_content = response['choices'][0]['message']['content']
#         generated_content = response.choices[0].message.content.strip()

#         try:
#             # Ensure the content is valid JSON
#             questions = json.loads(generated_content)
#         except json.JSONDecodeError:
#             raise ValueError("The response from OpenAI is not valid JSON.")

#         return  questions

#     except openai.OpenAIError as e:
#         raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=f"Error parsing response: {ve}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# async def generate_questions_and_save(
#     question_type: str,
#     payload: dict,
#     db: Session,
#     current_user: str = Depends(get_current_user)

# ):
#     """Handles API calls for different question types and saves the results."""
#     try:
#         # Call OpenAI API to generate questions
#         response = await generate_questions(question_type, payload)
        
#         # Validate OpenAI response
#         questions_with_answers = response.get('questions', [])
#         if not questions_with_answers:
#             raise ValueError("No valid questions generated from OpenAI.")
        
#         # Generate a unique exam ID
#         exam_id = str(uuid.uuid4())

#         # Save the exam in the database
#         exam = Exam(
#             id=exam_id,
#             user_id=current_user.user_id,  # Extract just the user_id
#             class_id=payload.get("class_name"),
#             subject_name_id=payload.get("subject_name"),
#             chapter_name_id=payload.get("chapter_name"),
#             topic_name_id=payload.get("topic_name"),
#             exam_title=f"{payload.get('topic_name', 'General')} {question_type.capitalize()} Quiz",
#             exam_description=f"A {question_type.capitalize()} quiz for educational purposes.",
#             questions_with_answers=questions_with_answers,
#             status="draft",
#             created_at=datetime.utcnow(),
#         )
#         db.add(exam)
#         db.commit()
#         db.refresh(exam)

#         return create_response(
#             success=True,
#             message="Questions generated and exam saved successfully.",
#             data={
#                 "exam_id": exam.id,
#                 "questions": questions_with_answers,
#             },
#             status_code=200
#         )

#     except ValueError as ve:
#         db.rollback()
#         raise HTTPException(status_code=400, detail=str(ve))
#     except openai.OpenAIError as oe:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(oe)}")
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")

# # Define API endpoints
# @router.post("/questions/objective")
# async def get_objective_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
#     return await generate_questions_and_save("objective", request.dict(), db, current_user)

# @router.post("/true_false")
# async def get_true_false_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
#     return await generate_questions_and_save("true_false", request.dict(), db, current_user)

# @router.post("/fill_in_blank")
# async def get_fill_in_blank_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
#     return await generate_questions_and_save("fill_in_blank", request.dict(), db, current_user)

# @router.post("/descriptive")
# async def get_descriptive_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
#     return await generate_questions_and_save("descriptive", request.dict(), db, current_user)

# @router.post("/mixed")
# async def get_mixed_questions(request: MixedQuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
#     return await generate_questions_and_save("mixed", request.dict(), db, current_user)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Exam
from database import get_db
from services.auth import get_current_user
from pydantic import BaseModel
from typing import Optional, Dict
import openai
import os
import json
from dotenv import load_dotenv
from services.classes import create_response
from datetime import datetime
import uuid

load_dotenv()
router = APIRouter()

class QuestionRequest(BaseModel):
    class_name: str
    subject_name: str
    chapter_name: Optional[str] = None  
    topic_name: Optional[str] = None 
    num_questions: int = 5
    difficulty: str = "medium"

class MixedQuestionRequest(QuestionRequest):
    question_distribution: Dict[str, int]

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

async def generate_questions(question_type: str, payload: dict):
    messages = [
        {"role": "system", "content": "You are an educational assistant that generates quiz questions in valid JSON format."}
    ]

    question_prompts = {
        "objective": f"Generate exactly {payload['num_questions']} objective (multiple-choice) questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Objective Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'objective', 'text': 'Your question here.', 'options': ['Option1', 'Option2', 'Option3', 'Option4'], 'marks': 2, 'correct_answer': {{'option_index': correct_option_index}} }}]}}.",        
        "true_false": f"Generate exactly {payload['num_questions']} true/false questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} True/False Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'true_false', 'text': 'Your question here.', 'marks': 1, 'correct_answer': true/false }}]}}.",    
        "fill_in_blank": f"Generate exactly {payload['num_questions']} fill-in-the-blank questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Fill-in-the-blank Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'fill_in_blank', 'text': 'Your question here with ____', 'marks': 2, 'correct_answer': {{'answers': ['Correct Answer']}} }}]}}.",        
        "descriptive": f"Generate exactly {payload['num_questions']} descriptive questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Descriptive Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'descriptive', 'text': 'Your question here.', 'marks': 5, 'correct_answer': {{'criteria': 'Expected key points'}} }}]}}.",        
        "mixed": f"Generate a mixed exam for Class {payload['class_name']} on the subject_name '{payload['subject_name']}', chapter_name '{payload['chapter_name']}', and topic_name '{payload.get('topic_name', 'general')}' with the following distribution: {payload.get('question_distribution', {})}. Include objective, true/false, fill-in-the-blank, and descriptive questions as specified. Return the response in JSON format with the structure: {{'exam_title': '{payload.get('topic_name', 'General')} Mixed Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'question_type', 'text': 'Your question here.', 'marks': question_marks, 'correct_answer': {{'answer_key': 'expected value based on type'}} }}]}}."
    }

    if question_type not in question_prompts:
        raise ValueError(f"Unsupported question type: {question_type}")

    messages.append({"role": "user", "content": question_prompts[question_type]})

    try:
        response = openai.chat.completions.create(
            model="gpt-4", 
            messages=messages,
            temperature=0,
            max_tokens=2000
        )
        
        # Log the entire response for debugging
        print(f"OpenAI Response: {response}")

        generated_content = response.choices[0].message.content.strip()
        print(f"Generated content: {generated_content}")

        questions = json.loads(generated_content)

        if not questions:
            raise ValueError("No valid questions generated.")
        return questions

    except openai.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format from OpenAI response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def generate_questions_and_save(question_type: str, payload: dict, db: Session, current_user: str = Depends(get_current_user)):
    try:
        response = await generate_questions(question_type, payload)
        questions_with_answers = response.get('questions', [])
        if not questions_with_answers:
            raise ValueError("No valid questions generated.")

        exam_id = str(uuid.uuid4())  # Convert UUID to string

        exam = Exam(
            id=exam_id,
            user_id=str(current_user.user_id),  # Convert UUID to string
            class_id=payload.get("class_name"),
            subject=payload.get("subject_name"),
            chapter=payload.get("chapter_name"),
            topic_name=payload.get("topic_name"),
            exam_title=f"{payload.get('topic_name', 'General')} {question_type.capitalize()} Quiz",
            exam_description=f"A {question_type.capitalize()} quiz.",
            questions_with_answers=questions_with_answers,
            status="draft",
            created_at=datetime.utcnow(),
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return create_response(
            success=True,
            message="Questions generated and saved successfully.",
            data={
                "exam_id": str(exam.id),  # Convert UUID to string
                "questions": questions_with_answers,
            },
            status_code=200
        )

    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except openai.OpenAIError as oe:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(oe)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/questions/objective")
async def get_objective_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await generate_questions_and_save("objective", request.dict(), db, current_user)

@router.post("/true_false")
async def get_true_false_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await generate_questions_and_save("true_false", request.dict(), db, current_user)

@router.post("/fill_in_blank")
async def get_fill_in_blank_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await generate_questions_and_save("fill_in_blank", request.dict(), db, current_user)

@router.post("/descriptive")
async def get_descriptive_questions(request: QuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await generate_questions_and_save("descriptive", request.dict(), db, current_user)

@router.post("/mixed")
async def get_mixed_questions(request: MixedQuestionRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return await generate_questions_and_save("mixed", request.dict(), db, current_user)
