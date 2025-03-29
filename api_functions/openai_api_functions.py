from config.config import OPENAI_API_KEY
from openai import OpenAI

def generate_llm_response(system_prompt: str, user_text: str, model: str = "gpt-4o-mini") -> str:
    """
    Generate a response from the OpenAI API
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content.strip()