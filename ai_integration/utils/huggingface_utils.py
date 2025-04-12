from transformers import pipeline
from typing import Optional

def huggingface_text_completion(prompt: str, model: str = "gpt2") -> Optional[str]:
    try:
        generator = pipeline("text-generation", model=model)
        result = generator(prompt, max_length=100, num_return_sequences=1)
        return result[0]["generated_text"]
    except Exception as e:
        print(f"HuggingFace Error: {e}")
        return None