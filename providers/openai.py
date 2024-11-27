#!filepath providers/openai.py
import logging
from typing import List, Dict, Any, Optional
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openai
from config.settings import settings
from providers.base import BaseProvider, Message, ModelResponse

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self) -> None:
        """Initialize OpenAI client with API key from settings."""
        openai.api_key = settings.OPENAI_API_KEY
        self.available_models = settings.OPENAI_AVAILABLE_MODELS
        self.default_model = settings.OPENAI_DEFAULT_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    async def generate_response(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """
        Generate a response using OpenAI's API.

        Args:
            messages: List of conversation messages.
            model: OpenAI model to use. Defaults to settings.
            temperature: Response randomness. Defaults to settings.
            max_tokens: Max tokens to generate. Defaults to settings.

        Returns:
            ModelResponse: Generated response with metadata.

        Raises:
            Exception: If API call fails or response is invalid.
        """
        try:
            formatted_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = await openai.ChatCompletion.create(
                model=model or self.default_model,
                messages=formatted_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            if not response.choices:
                raise ValueError("No response generated from OpenAI")

            first_choice = response.choices[0]
            
            return ModelResponse(
                content=first_choice.message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=first_choice.finish_reason
            )

        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {str(e)}")
            raise

    async def validate_model(self, model: str) -> bool:
        """
        Validate if a model is available.

        Args:
            model: Model identifier to validate.

        Returns:
            bool: True if model is valid and available.
        """
        return model in self.available_models

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models.

        Returns:
            List[str]: List of available model identifiers.
        """
        return self.available_models

if __name__ == "__main__":
    import asyncio
    
    async def test_openai_provider():
        provider = OpenAIProvider()
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Write a short greeting!")
        ]
        
        try:
            response = await provider.generate_response(messages)
            print(f"Response: {response.content}")
            print(f"Model: {response.model}")
            print(f"Usage: {response.usage}")
        except Exception as e:
            print(f"Error: {str(e)}")

    asyncio.run(test_openai_provider())
