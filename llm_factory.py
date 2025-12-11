import os
from enum import Enum
from typing import Any, Dict
from dotenv import load_dotenv
from groq import Groq
#from google import genai

"""
llm_factory.py

LLM Factory class to simplify interactions with different LLM models.
"""

load_dotenv()


class ModelCatalogue(Enum):
    """Enum class defining available models."""
    LLAMA_70B = "llama-3.3-70b-versatile"
    LLAMA_8B = "llama-3.1-8b-instant"
    GPT_OSS = "openai/gpt-oss-120b"
    GEMINI_FLASH = "gemini-2.5-flash"


class LLMFactory:
    """
    A simple factory for interacting with LLM models.

    Usage:
        factory = LLMFactory(model=ModelCatalogue.LLAMA_70B)
        factory.set_system_message("You are a helpful assistant.")
        response = factory.send_to_llm("What do you know about Messi?")
        print(response)
    """

    def __init__(self, model: ModelCatalogue) -> None:
        """
        Initialize the LLM factory.

        Args:
            model: The model to use from ModelCatalogue
        """
        self.model = model
        self.system_message = "You are a helpful assistant."
        self.client = None
        
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the appropriate client based on the model."""
        if self.model in [ModelCatalogue.LLAMA_70B, ModelCatalogue.LLAMA_8B, ModelCatalogue.GPT_OSS]:
            # Groq models
            api_key = os.getenv("GROK_API_KEY")
            if not api_key:
                raise ValueError("GROK_API_KEY not found in environment variables")
            self.client = Groq(api_key=api_key)
        # elif self.model == ModelCatalogue.GEMINI_FLASH:
        #     # Google Gemini model
        #     self.client = genai.Client()
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def set_system_message(self, system_message: str) -> None:
        """
        Set the system message for the assistant.

        Args:
            system_message: System prompt to set assistant behavior
        """
        self.system_message = system_message

    def send_to_llm(self, user_message: str) -> str:
        """
        Send a message to the LLM and get the response.

        Args:
            user_message: The user's message/question

        Returns:
            The model's response as a string
        """
        if self.model in [ModelCatalogue.LLAMA_70B, ModelCatalogue.LLAMA_8B, ModelCatalogue.GPT_OSS]:
            # Groq models
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_message
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                model=self.model.value
            )
            print(self.system_message,user_message)
            return chat_completion.choices[0].message.content
        
        # elif self.model == ModelCatalogue.GEMINI_FLASH:
        #     # Google Gemini model
        #     response = self.client.models.generate_content(
        #         model=self.model.value,
        #         contents=user_message
        #     )
        #     return response.text

    def get_client(self) -> Any:
        """
        Get the initialized client.

        Returns:
            The client instance (Groq or genai.Client)
        """
        return self.client


__all__ = ["LLMFactory", "ModelCatalogue"]