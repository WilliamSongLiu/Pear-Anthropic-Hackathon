from llm_openai import OpenaiLLM
from llm_anthropic import AnthropicLLM

def make_llm(company, model, temperature=None):
    if company == "openai":
        return OpenaiLLM(model, temperature)
    elif company == "anthropic":
        return AnthropicLLM(model, temperature)
    return None