# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# # from services.questions import generate_questions
# from typing import Optional
# import openai
# import os
# from fastapi import HTTPException

# # Define the router
# router = APIRouter()

# class QuestionRequest(BaseModel):
#     class_level: str
#     subject: str
#     chapter: Optional[str] = None  
#     topic: Optional[str] = None 
#     num_questions: int = 5
#     difficulty: str = "medium"

# class MixedQuestionRequest(QuestionRequest):
#     question_distribution: dict

# @router.post("/questions/objective")
# async def get_objective_questions(request: QuestionRequest):
#     return await generate_questions("objective", request.dict())

# @router.post("/true_false")
# async def get_true_false_questions(request: QuestionRequest):
#     return await generate_questions("true_false", request.dict())

# @router.post("/fill_in_blank")
# async def get_fill_in_blank_questions(request: QuestionRequest):
#     return await generate_questions("fill_in_blank", request.dict())

# @router.post("/descriptive")
# async def get_descriptive_questions(request: QuestionRequest):
#     return await generate_questions("descriptive", request.dict())

# @router.post("/mixed")
# async def get_mixed_questions(request: MixedQuestionRequest):
#     return await generate_questions("mixed", request.dict())

# # Set the API key
# openai.api_key = os.getenv("OPENAI_API_KEY")
# if not openai.api_key:
#     raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# async def generate_questions(question_type, payload):
#     """Handles API calls for different question types."""
#     messages = [
#         {
#             "role": "system",
#             "content": "You are an educational assistant that generates quiz questions in valid JSON format."
#         }
#     ]

#     question_prompts = {
#         "objective": f"Generate exactly {payload['num_questions']} objective (multiple-choice) questions for Class {payload['class_level']} on the subject '{payload['subject']}' and the topic '{payload.get('topic', 'general')}'. Return the response in JSON format with 'question', 'options', and 'correct_answer' for each question.",
#         "true_false": f"Generate exactly {payload['num_questions']} true/false questions for Class {payload['class_level']} on the subject '{payload['subject']}'. Return the response in JSON format as a list with 'question' and 'correct_answer'.",
#         "fill_in_blank": f"Generate exactly {payload['num_questions']} fill-in-the-blank questions for Class {payload['class_level']} on '{payload.get('topic', 'general')}'. Return the response in JSON format.",
#         "descriptive": f"Generate exactly {payload['num_questions']} descriptive questions for Class {payload['class_level']}. Return the response in JSON format.",
#         "mixed": f"Generate a mixed exam for Class {payload['class_level']} on '{payload.get('topic', 'general')}' with distribution {payload.get('question_distribution', {})}. Return the response in JSON format."
#     }

#     if question_type not in question_prompts:
#         raise ValueError(f"Unsupported question type: {question_type}")

#     messages.append({"role": "user", "content": question_prompts[question_type]})

#     try:
#         # Call the OpenAI API for chat completions
#         response = openai.ChatCompletion.create(
#             model="gpt-4",  # Replace with your actual model
#             messages=messages,
#             temperature=0,
#             max_tokens=2000
#         )

#         # Extract the generated content
#         generated_content = response['choices'][0]['message']['content']

#         return {"questions": eval(generated_content)}

#     except openai.OpenAIError as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=f"Error parsing response: {ve}")


# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import Optional, Dict
# import openai
# import os
# import json

# # Define the router
# router = APIRouter()

# # Define request models
# class QuestionRequest(BaseModel):
#     class_level: str
#     subject: str
#     chapter: Optional[str] = None  
#     topic: Optional[str] = None 
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
#         "objective": f"Generate exactly {payload['num_questions']} objective (multiple-choice) questions for Class {payload['class_level']} on the subject '{payload['subject']}' and the topic '{payload.get('topic', 'general')}'. Return the response in JSON format with 'question', 'options', and 'correct_answer' for each question.",
#         "true_false": f"Generate exactly {payload['num_questions']} true/false questions for Class {payload['class_level']} on the subject '{payload['subject']}'. Return the response in JSON format as a list with 'question' and 'correct_answer'.",
#         "fill_in_blank": f"Generate exactly {payload['num_questions']} fill-in-the-blank questions for Class {payload['class_level']} on '{payload.get('topic', 'general')}'. Return the response in JSON format.",
#         "descriptive": f"Generate exactly {payload['num_questions']} descriptive questions for Class {payload['class_level']}. Return the response in JSON format.",
#         "mixed": f"Generate a mixed exam for Class {payload['class_level']} on '{payload.get('topic', 'general')}' with distribution {payload.get('question_distribution', {})}. Return the response in JSON format."
#     }

#     if question_type not in question_prompts:
#         raise ValueError(f"Unsupported question type: {question_type}")

#     messages.append({"role": "user", "content": question_prompts[question_type]})

#     try:
#         # Call the OpenAI API for chat completions
#         response = openai.ChatCompletion.create(
#             model="gpt-4", 
#             messages=messages,
#             temperature=0,
#             max_tokens=2000
#         )

#         # Extract the generated content and validate as JSON
#         generated_content = response['choices'][0]['message']['content']

#         try:
#             # Ensure the content is valid JSON
#             questions = json.loads(generated_content)
#         except json.JSONDecodeError:
#             raise ValueError("The response from OpenAI is not valid JSON.")

#         return {"questions": questions}

#     except openai.OpenAIError as e:
#         raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=f"Error parsing response: {ve}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# # Define API routes
# @router.post("/questions/objective")
# async def get_objective_questions(request: QuestionRequest):
#     return await generate_questions("objective", request.dict())

# @router.post("/true_false")
# async def get_true_false_questions(request: QuestionRequest):
#     return await generate_questions("true_false", request.dict())

# @router.post("/fill_in_blank")
# async def get_fill_in_blank_questions(request: QuestionRequest):
#     return await generate_questions("fill_in_blank", request.dict())

# @router.post("/descriptive")
# async def get_descriptive_questions(request: QuestionRequest):
#     return await generate_questions("descriptive", request.dict())

# @router.post("/mixed")
# async def get_mixed_questions(request: MixedQuestionRequest):
#     return await generate_questions("mixed", request.dict())
