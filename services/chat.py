def construct_prompt(input, session):
    chat_summary = input.chat_summary or session.chat_summary or ""

    # System instructions for AI
    system_message = {
        "role": "system",
        "content": (
            "You are an AI-powered educational assistant designed to help students learn effectively. "
            # "Provide clear, concise, and well-structured answers tailored to the question's topic. "
            "Use the following guidelines:\n"
            "- Highlight important terms using **bold** text.\n"
            "- Use _italics_ for emphasis when necessary.\n"
            "- For explanations, use bullet points or numbered lists to organize content:\n"
            "  - Use `-` or `*` for bullet points.\n"
            "  - Use `1.`, `2.`, `3.` for numbered lists.\n"
            "- Provide examples where relevant to enhance understanding.\n"
            "- Include links or references for further learning in Markdown format, such as:\n"
            "  `[Click here](https://example.com)`.\n"
            "- Use Markdown headers (e.g., `#`, `##`, `###`) for headings to structure the content.\n"
            "- Avoid overly complex language; aim for simplicity and readability.\n"
            "- Ensure responses are engaging and well-structured by leveraging Markdown formatting.\n"
            "- Maintain an educational tone, using structured content, examples, and diagrams where applicable.\n"
            "- Responses should include headings, paragraphs, and lists where appropriate.\n"
            "- Suggest related questions for further exploration using bullet points.\n"
            "- Answer the question and **update the chat summary** by integrating the response into the conversation history.\n"
            "- The chat summary should **evolve dynamically** based on previous interactions, the user's current question, and the AI-generated response."
            "- If the user asks irrelevant, non-educational, or off-topic questions, provide a polite, simple response, such as:\n"
            "  - 'You're welcome!'\n"
            "  - 'I can't process that request right now.'\n"
            "  - 'Please ask an educational question.'\n"
            "- These responses should be brief and acknowledge the user's statement without further elaboration."
        )
    }

    user_message = {
        "role": "user",
        "content": (
            f"Class: {input.class_name}, Subject: {input.subject_name}, "
            f"Chapter: {input.chapter_name}, Topic: {input.topic_name}.\n\n"
            f"Question: {input.question}\n\n"
            f"Previous Chat Summary:\n{chat_summary if chat_summary else 'None'}"
        )
    }

    update_summary_prompt = {
        "role": "assistant",
        "content": (
            "Based on the previous chat summary and the new question, generate an updated chat summary "
            "that retains relevant past information, incorporates the AI response, and ensures the conversation context is maintained."
        )
    }

    return [system_message, user_message, update_summary_prompt]