# import requests
# import os

# OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# HEADERS = {
#     "Authorization": f"Bearer {OPENAI_API_KEY}",
#     "Content-Type": "application/json"
# }

# async def generate_questions(question_type, payload):
#     """Handles API calls for different question types."""
#     messages = [{"role": "system", "content": "You are an educational assistant that generates quiz questions in valid JSON format."}]
    
#     question_prompts = {
#         "objective": f"Generate {payload['num_questions']} objective (multiple-choice) questions for Class {payload['class_level']} on the subject '{payload['subject']}' and the topic '{payload['topic']}'...",
#         "true_false": f"Generate {payload['num_questions']} true/false questions for Class {payload['class_level']} on the subject '{payload['subject']}'...",
#         "fill_in_blank": f"Generate {payload['num_questions']} fill in the blank questions for Class {payload['class_level']} on '{payload['topic']}'...",
#         "descriptive": f"Generate {payload['num_questions']} descriptive questions for Class {payload['class_level']}...",
#         "mixed": f"Generate a mixed exam for Class {payload['class_level']} on '{payload['topic']}' with distribution {payload['question_distribution']}..."
#     }
    
#     if question_type not in question_prompts:
#         raise ValueError(f"Unsupported question type: {question_type}")

#     messages.append({"role": "user", "content": question_prompts[question_type]})

#     try:
#         response = requests.post(
#             OPENAI_API_URL,
#             headers=HEADERS,
#             json={"model": "gpt-4", "temperature": 0, "max_tokens": 2000, "messages": messages}
#         )
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=str(e))

# import requests
# import os
# from fastapi import HTTPException

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# HEADERS = {
#     "Authorization": f"Bearer {OPENAI_API_KEY}",
#     "Content-Type": "application/json"
# }

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

#     messages.append(
#         {
#         "role": "user", 
#         "content": question_prompts[question_type]
#         }
#     )

#     try:
#         response = requests.post(
#             headers=HEADERS,
#             json={
#             "model": "gpt-4", 
#             "temperature": 0, 
#             "max_tokens": 2000, 
#             "messages": messages
#             }
#         )
#         response.raise_for_status()
#         result = response.json()

#         # Extract generated content
#         generated_content = result.get("choices", [])[0].get("message", {}).get("content", "[]")
        
#         # Parse and validate the response
#         questions = eval(generated_content)  # Be cautious with eval; better to use json.loads if JSON format is guaranteed.
#         if not isinstance(questions, list) or len(questions) != payload['num_questions']:
#             raise ValueError(f"Expected {payload['num_questions']} questions but got {len(questions)} or invalid response format.")

#         return {"questions": questions}

#     except requests.exceptions.RequestException as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=f"Error parsing response: {ve}")


# import openai
# import os
# from fastapi import HTTPException

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
