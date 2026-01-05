import logging
import os
from abc import abstractmethod, ABC

from google import genai
import openai
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMBackend(ABC):
    @abstractmethod
    def generate_score(self, prompt: str) -> float:
        pass


class GeminiBackend(LLMBackend):
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY')
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = getattr(settings, 'GEMINI_MODEL')
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY not found.")

    def generate_score(self, prompt: str) -> float:
        if not self.client:
            return 0.0
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            print(response.text.strip())
            return float(response.text.strip())
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return 0.0


class OpenAIBackend(LLMBackend):
    def __init__(self):
        api_key = getattr(settings, 'OPENAI_API_KEY')
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.model_name = getattr(settings, 'OPENAI_MODEL')
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found.")

    def generate_score(self, prompt: str) -> float:
        if not self.client:
            return 0.0
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            content = response.choices[0].message.content.strip()
            return float(content)
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            return 0.0
