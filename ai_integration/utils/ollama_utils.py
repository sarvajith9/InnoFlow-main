import requests
from typing import Optional

def ollama_text_completion(prompt: str, model: str = "llama2", base_url: str = "http://localhost:11434") -> Optional[str]:
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"Ollama API Error: {e}")
        return None