from fastapi import HTTPException
import json
from dotenv import load_dotenv
import openai
import os
import re
from datetime import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

async def generate_questions(question_type: str, payload: dict):
    messages = [
        {"role": "system", "content": "You are an educational assistant that generates quiz questions in valid JSON format."}
    ]

    question_prompts = {
        "objective": f"Generate exactly {payload['num_questions']} objective (multiple-choice) questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Objective Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'objective', 'text': 'Your question here.', 'options': ['Option1', 'Option2', 'Option3', 'Option4'], 'marks': 2, 'correct_answer': {{'option_index': correct_option_index}} }}]}}.",
        "true_false": f"Generate exactly {payload['num_questions']} true/false questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} True/False Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'true_false', 'text': 'Your question here.', 'marks': 1, 'correct_answer':{{'value': true/false}} }}]}}.",
        "fill_in_blank": f"Generate exactly {payload['num_questions']} fill-in-the-blank questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Fill-in-the-blank Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'fill_in_blank', 'text': 'Your question here with ____', 'marks': 2, 'correct_answer': {{'answers': 'Correct Answer'}} }}]}}.",
        "descriptive": f"Generate exactly {payload['num_questions']} descriptive questions for Class {payload['class_name']} on the subject_name '{payload['subject_name']}' and the topic_name '{payload.get('topic_name', 'general')}'. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Descriptive Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': [{{'id': 'q1', 'type': 'descriptive', 'text': 'Your question here.', 'marks': 5, 'correct_answer': {{'criteria': 'Expected key points'}} }}]}}.",
        "mixed": (
            f"Generate a mixed exam for Class {payload['class_name']} on the subject '{payload['subject_name']}'.\n"
            f"Chapters and topics: {json.dumps(payload['chapters'])}\n"
            f"Question distribution: {json.dumps(payload['question_distribution'])}\n\n"
            "Return the response in JSON format with this structure:\n"
            "{\n"
            '  "exam_title": "{chapter_name} Mixed Quiz",\n'
            '  "class_name": "{class_name}",\n'
            '  "subject_name": "{subject_name}",\n'
            '  "chapters": [\n'
            "    {\n"
            '      "chapter_name": "string",\n'
            '      "topics": ["string"]\n'
            "    }\n"
            "  ],\n"
            '  "total_questions": total number of questions,\n'
            '  "total_marks": total marks,\n'
            '  "total_time": estimated time in minutes,\n'
            '  "questions": {\n'
            '    "objective": [\n'
            "      {\n"
            '        "id": "string",\n'
            '        "type": "objective",\n'
            '        "text": "string",\n'
            '        "options": ["string", "string", "string", "string"],\n'
            '        "marks": 2,\n'
            '        "correct_answer": {\n'
            '          "option_index": integer\n'
            "        }\n"
            "      }\n"
            "    ],\n"
            '    "true_false": [\n'
            "      {\n"
            '        "id": "string",\n'
            '        "type": "true_false",\n'
            '        "text": "string",\n'
            '        "marks": 1,\n'
            '        "correct_answer": {\n'
            '          "value": boolean\n'
            "        }\n"
            "      }\n"
            "    ],\n"
            '    "fill_in_blank": [\n'
            "      {\n"
            '        "id": "string",\n'
            '        "type": "fill_in_blank",\n'
            '        "text": "string",\n'
            '        "marks": 2,\n'
            '        "correct_answer": {\n'
            '          "answers": "string"\n'
            "        }\n"
            "      }\n"
            "    ],\n"
            '    "descriptive": [\n'
            "      {\n"
            '        "id": "string",\n'
            '        "type": "descriptive",\n'
            '        "text": "string",\n'
            '        "marks": 5,\n'
            '        "correct_answer": {\n'
            '          "criteria": "string"\n'
            "        }\n"
            "      }\n"
            "    ]\n"
            "  }\n"
            "}"
        )
    }


    if question_type not in question_prompts:
        raise ValueError(f"Unsupported question type: {question_type}")

    messages.append({"role": "user", "content": question_prompts[question_type]})

    try:
        start_time = datetime.utcnow()
        response = openai.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages,
            temperature=0,
            max_tokens=3500
        )
        end_time = datetime.utcnow()
        # Correct way to access token usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        gen_time = (end_time - start_time).total_seconds()

        generated_content = response.choices[0].message.content.strip()

        json_match = re.search(r"```json(.*?)```", generated_content, re.DOTALL)
        if json_match:
            cleaned_json = json_match.group(1).strip()
        else:
            cleaned_json = generated_content 

        questions = json.loads(cleaned_json) 
        return questions, input_tokens, output_tokens, total_tokens, gen_time
   
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format from OpenAI response.")
    except openai.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format from OpenAI response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# async def evaluate_answers(questions_with_answers):
#     """ AI-based answer evaluation function """

#     messages = [
#         {"role": "system", "content": "You are an AI-based exam evaluator. Evaluate the student's answers strictly, assign marks for each question, provide status, provide feedback, and return the total score. The response must be in the following JSON format:"},
#         {"role": "user", "content": json.dumps({
#             "questions": [
#                 {
#                     "id": "q1",
#                     "marks_obtained": 2,
#                     "status": "correct",
#                     "feedback": "Correct answer. Good job!"
#                 }
#             ],
#             "score": 10,
#             "overall_feedback": "Great job! Keep practicing."
#         })}
#     ]

#     prompt = {"questions": questions_with_answers}

#     messages.append({"role": "user", "content": json.dumps(prompt)})

#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4o-mini", 
#             messages=messages,
#             temperature=0,
#             max_tokens=3000
#         )

#         evaluation_content = response.choices[0].message.content.strip()

#         json_match = re.search(r"```json(.*?)```", evaluation_content, re.DOTALL)
#         if json_match:
#             cleaned_json = json_match.group(1).strip()
#         else:
#             cleaned_json = evaluation_content  

#         evaluation = json.loads(cleaned_json)  

#         if "questions" not in evaluation or "score" not in evaluation:
#             raise ValueError("AI response does not contain 'questions' or 'score'. Ensure OpenAI follows the expected format.")

#         return evaluation

#     except json.JSONDecodeError:
#         raise HTTPException(status_code=400, detail="Error parsing OpenAI response JSON.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"AI evaluation error: {str(e)}")


# AI-based answer evaluation function
async def evaluate_answers(questions_with_answers):
    """AI-based answer evaluation function"""

    # Define the system message and example user message
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI-based exam evaluator. Evaluate the student's answers strictly, "
                "assign marks for each question, provide status, provide feedback, and return the total score. "
                "The response must be in the following JSON format:"
            ),
        },
        {
            "role": "user",
            "content": json.dumps({
                "questions": [
                    {
                        "id": "q1",
                        "marks_obtained": 2,
                        "status": "correct",
                        "feedback": "Correct answer. Good job!"
                    }
                ],
                "score": 10,
                "overall_feedback": "Great job! Keep practicing."
            }),
        },
    ]

    # Append the actual questions with answers to the messages
    prompt = {"questions": questions_with_answers}
    messages.append({"role": "user", "content": json.dumps(prompt)})

    try:
        # Make the API call to OpenAI's ChatCompletion endpoint
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0,
            max_tokens=3000,
        )

        # Extract the content from the response
        evaluation_content = response.choices[0].message.content.strip()

        # Attempt to extract JSON from the response content
        json_match = re.search(r"```json(.*?)```", evaluation_content, re.DOTALL)
        if json_match:
            cleaned_json = json_match.group(1).strip()
        else:
            cleaned_json = evaluation_content

        # Parse the JSON content
        evaluation = json.loads(cleaned_json)

        # Validate the presence of required keys in the evaluation
        if "questions" not in evaluation or "score" not in evaluation:
            raise ValueError(
                "AI response does not contain 'questions' or 'score'. Ensure OpenAI follows the expected format."
            )

        return evaluation

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error parsing OpenAI response JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI evaluation error: {str(e)}")
