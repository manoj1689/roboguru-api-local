from fastapi import HTTPException
import json
from dotenv import load_dotenv
import openai
import os


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
        "mixed": f"Generate a mixed exam for Class {payload['class_name']} on the subject '{payload['subject_name']}', chapter '{payload['chapter_name']}', and topic '{payload.get('topic_name', 'general')}' with the following distribution: {payload.get('question_distribution', {})}. Include objective, true/false, fill-in-the-blank, and descriptive questions as specified. Return the response in JSON format with the following structure: {{'exam_title': '{payload.get('topic_name', 'General')} Mixed Quiz', 'class': '{payload['class_name']}', 'subject_name': '{payload['subject_name']}', 'topic_name': '{payload.get('topic_name', 'general')}', 'questions': {{ 'objective': [{{'id': 'q1', 'type': 'objective', 'text': 'Your question here.', 'options': ['Option1', 'Option2', 'Option3', 'Option4'], 'marks': 2, 'correct_answer': {{'option_index': correct_option_index}} }}], 'true_false': [{{'id': 'q1', 'type': 'true_false', 'text': 'Your question here.', 'marks': 1, 'correct_answer':{{'value': true/false}} }}], 'fill_in_blank': [{{'id': 'q1', 'type': 'fill_in_blank', 'text': 'Your question here with ____', 'marks': 2, 'correct_answer': {{'answers': 'Correct Answer'}} }}], 'descriptive': [{{'id': 'q1', 'type': 'descriptive', 'text': 'Your question here.', 'marks': 5, 'correct_answer': {{'criteria': 'Expected key points'}} }}]}}}}."
        
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
        generated_content = response.choices[0].message.content.strip()
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


async def evaluate_answers(questions_with_answers):
    """ AI-based answer evaluation function """

    messages = [
        {"role": "system", "content": "You are an AI-based exam evaluator. Evaluate the student's answers strictly, assign marks for each question, provide feedback, and return the total score. The response must be in the following JSON format:"},
        {"role": "user", "content": json.dumps({
            "questions": [
                {
                    "id": "q1",
                    "marks_obtained": 2,
                    "feedback": "Correct answer. Good job!"
                }
            ],
            "score": 10,
            "overall_feedback": "Great job! Keep practicing."
        })}
    ]

    prompt = {"questions": questions_with_answers}

    messages.append({"role": "user", "content": json.dumps(prompt)})

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
            max_tokens=2000
        )

        evaluation_content = response.choices[0].message.content.strip()

        # Debugging: Print the AI response before parsing
        print("AI Response (Raw):", evaluation_content)

        # Ensure it's parsed correctly
        if not evaluation_content:
            raise ValueError("OpenAI returned an empty response.")

        if isinstance(evaluation_content, str):
            evaluation = json.loads(evaluation_content)  # Convert string to dict
        else:
            evaluation = evaluation_content  # Already a dict

        # Debugging: Check if evaluation contains expected fields
        if "questions" not in evaluation or "score" not in evaluation:
            raise ValueError("AI response does not contain 'questions' or 'score'. Ensure OpenAI follows the expected format.")

        return evaluation

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error parsing OpenAI response JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI evaluation error: {str(e)}")
