import os
import time
from enum import Enum
from typing import Any
from dotenv import load_dotenv
from groq import Groq
from google import genai
from openai import OpenAI
load_dotenv()

class ModelCatalogue(Enum):
    """Enum class defining available models."""
    LLAMA_70B = "llama-3.3-70b-versatile"
    LLAMA_8B = "llama-3.1-8b-instant"
    GPT_OSS = "openai/gpt-oss-120b"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    GEMINI_FLASH = "gemini-2.5-flash"


class LLMFactory:
    """
    A simple factory for interacting with LLM models.
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
        self.provider = None
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.max_retries = 5
        self.initial_retry_delay = 10  # seconds

        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the appropriate client based on the model."""

        # -------- Groq Models --------
        if self.model in {
            ModelCatalogue.LLAMA_70B,
            ModelCatalogue.LLAMA_8B,
            ModelCatalogue.GPT_OSS,
        }:
            api_key = os.getenv("GROK_API_KEY")
            if not api_key:
                raise ValueError("GROK_API_KEY not found in environment variables")

            self.client = Groq(api_key=api_key)
            self.provider = "groq"

        # -------- OpenAI Models --------
        elif self.model in {
            ModelCatalogue.GPT_35_TURBO,
            ModelCatalogue.GPT_4,
        }:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            self.client = OpenAI(api_key=api_key)
            self.provider = "openai"

        # -------- Gemini Models --------
        elif self.model == ModelCatalogue.GEMINI_FLASH:
            self.client = genai.Client()
            self.provider = "gemini"

        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def set_system_message(self, system_message: str) -> None:
        self.system_message = system_message

    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff for handling overloaded models.
        
        Args:
            func: The function to retry
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            The result of the function call
        """
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                # Check if it's a 503 overload error or similar
                if '503' in error_msg or '429' in error_msg or 'overloaded' in error_msg.lower() or 'UNAVAILABLE' in error_msg:
                    if attempt < self.max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = self.initial_retry_delay * (2 ** attempt)
                        print(f"⚠️  Model overloaded. Waiting {delay} seconds before retry {attempt + 1}/{self.max_retries}...")
                        time.sleep(delay)
                    else:
                        print(f"❌ Max retries ({self.max_retries}) reached. Model still unavailable.")
                        raise
                else:
                    # If it's not an overload error, raise immediately
                    raise

    def send_to_llm(self, user_message: str) -> str:
        """
        Send a message to the LLM and get the response with automatic retry on overload.
        """

        # -------- Groq --------
        if self.provider == "groq":
            def _make_groq_call():
                chat_completion = self.client.chat.completions.create(
                    model=self.model.value,
                    messages=[
                        {"role": "system", "content": self.system_message},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0
                )
                # Track tokens for Groq
                if hasattr(chat_completion, 'usage') and chat_completion.usage:
                    self.total_input_tokens += chat_completion.usage.prompt_tokens
                    self.total_output_tokens += chat_completion.usage.completion_tokens
                return chat_completion.choices[0].message.content
            
            return self._retry_with_backoff(_make_groq_call)

        # -------- OpenAI --------
        elif self.provider == "openai":
            def _make_openai_call():
                response = self.client.chat.completions.create(
                    model=self.model.value,
                    messages=[
                        {"role": "system", "content": self.system_message},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0
                )
                # Track tokens for OpenAI
                if hasattr(response, 'usage') and response.usage:
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens
                return response.choices[0].message.content
            
            return self._retry_with_backoff(_make_openai_call)

        # -------- Gemini --------
        elif self.provider == "gemini":
            def _make_gemini_call():
                response = self.client.models.generate_content(
                    model=self.model.value,
                    contents=user_message,
                    temperature=0,
                )
                # Track tokens for Gemini
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    self.total_input_tokens += response.usage_metadata.prompt_token_count
                    self.total_output_tokens += response.usage_metadata.candidates_token_count
                return response.text
            
            return self._retry_with_backoff(_make_gemini_call)

        else:
            raise RuntimeError("LLM provider not initialized correctly")

    def get_client(self) -> Any:
        return self.client

    def get_token_usage(self) -> dict[str, int]:
        """
        Get the total token usage for all API calls made with this factory instance.
        
        Returns:
            Dictionary with 'input_tokens' and 'output_tokens' counts
        """
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens
        }

    def reset_token_usage(self) -> None:
        """
        Reset the token counters to zero.
        """
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def print_token_usage(self) -> None:
        """
        Print a formatted summary of token usage.
        """
        usage = self.get_token_usage()
        print("=" * 50)
        print("Token Usage Summary")
        print("=" * 50)
        print(f"Input tokens:  {usage['input_tokens']:,}")
        print(f"Output tokens: {usage['output_tokens']:,}")
        print(f"Total tokens:  {usage['total_tokens']:,}")
        print("=" * 50)