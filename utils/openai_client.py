from openai import OpenAI
from dotenv import load_dotenv
import os
from schemas import ChatStructuredResponse


load_dotenv()

MODEL = "gpt-4o-mini"

# Set up OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not openai_client.api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")



def get_ai_response(messages):
    """Call OpenAI API and return structured response, input tokens, and output tokens."""
    completion = openai_client.beta.chat.completions.parse(
        model=MODEL,
        messages=messages,
        response_format=ChatStructuredResponse,
    )

    if not completion.choices:
        return None, 0, 0

    structured_data = completion.choices[0].message.parsed
    usage_data = completion.usage

    input_tokens = getattr(usage_data, "input_tokens", 0)
    output_tokens = getattr(usage_data, "output_tokens", 0)

    return structured_data, input_tokens, output_tokens
