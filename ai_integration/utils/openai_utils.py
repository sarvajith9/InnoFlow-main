import openai
from django.conf import settings
from typing import Optional

def openai_text_completion(prompt: str, model: str = "gpt-3.5-turbo") -> Optional[str]:
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None