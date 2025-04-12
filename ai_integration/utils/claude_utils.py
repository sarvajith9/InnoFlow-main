import anthropic
from django.conf import settings
from typing import Optional

def claude_text_completion(prompt: str, model: str = "claude-2") -> Optional[str]:
    try:
        client = anthropic.Client(settings.ANTHROPIC_API_KEY)
        response = client.completions.create(
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
            model=model,
            max_tokens_to_sample=1000
        )
        return response.completion
    except Exception as e:
        print(f"Claude API Error: {e}")
        return None