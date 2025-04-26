from abc import ABC, abstractmethod

class LLM(ABC):
    @abstractmethod
    def __init__(self, model):
        pass

    @abstractmethod
    def get_completion(self, messages, tools=None, response_format=None, temperature=None):
        pass