from llm_abstract import LLM
import os
from dotenv import load_dotenv
from openai import OpenAI

class OpenaiLLM(LLM):
    def __init__(self, model, temperature):
        self.model = model
        self.temperature = temperature
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_completion(self, messages, tools=None, response_format=None):
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            max_completion_tokens=10000,
            messages=messages,
            **({"tools": tools} if tools is not None else {}),
            **({"response_format": response_format} if response_format is not None else {}),
            **({"temperature": self.temperature} if self.temperature is not None else {})
        )

        content = response.choices[0].message.content
        tool_call = None
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0].function.arguments

        return content, tool_call