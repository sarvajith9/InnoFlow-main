from celery import shared_task
from time import time
from .models import AIModelConfig, ModelComparison, ModelResponse
from .utils import (
    openai_utils,
    claude_utils,
    deepseek_utils,
    ollama_utils,
    huggingface_utils
)

@shared_task
def run_ai_model_task(model_config_id: int, prompt: str, comparison_id: int) -> str:
    model_config = AIModelConfig.objects.get(id=model_config_id)
    
    start_time = time()
    
    if model_config.provider == 'OPENAI':
        response = openai_utils.openai_text_completion(prompt, model_config.model_name)
    elif model_config.provider == 'ANTHROPIC':
        response = claude_utils.claude_text_completion(prompt, model_config.model_name)
    elif model_config.provider == 'DEEPSEEK':
        response = deepseek_utils.deepseek_text_completion(prompt, model_config.model_name)
    elif model_config.provider == 'OLLAMA':
        response = ollama_utils.ollama_text_completion(prompt, model_config.model_name, model_config.base_url)
    elif model_config.provider == 'HUGGINGFACE':
        response = huggingface_utils.huggingface_text_completion(prompt, model_config.model_name)
    else:
        response = f"Unsupported model provider: {model_config.provider}"
    
    latency = time() - start_time
    
    if response is None:
        response = "Error occurred while generating response"
    
    # Save the response
    comparison = ModelComparison.objects.get(id=comparison_id)
    ModelResponse.objects.create(
        comparison=comparison,
        model_config=model_config,
        response=response,
        latency=latency
    )
    
    return response