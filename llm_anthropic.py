from llm_abstract import LLM
import os
from dotenv import load_dotenv
from anthropic import Anthropic

class AnthropicLLM(LLM):
	def __init__(self, model, temperature):
		self.model = model
		self.temperature = temperature
		load_dotenv()
		self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

	def get_completion(self, messages, tools=None, response_format=None):
		if messages[0]["role"] != "system":
			raise Exception("First message not system")

		response = self.client.messages.create(
			model=self.model,
			max_tokens=1000,
			system=messages[0]["content"],
			messages=messages[1:],
			**({"tools": tools} if tools is not None else {}),
            **({"response_format": response_format} if response_format is not None else {}),
			**({"temperature": self.temperature} if self.temperature is not None else {})
		)

		content = None
		tool_call = None
		for block in response.content:
			if block.type == "tool_use":
				tool_call = block.input
			else:
				content = block.text

		return content, tool_call