"""
Base class for AI providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str
    content: str
    name: Optional[str] = None


@dataclass
class ModelResponse:
    """Represents a response from the AI model."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None


class BaseProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ModelResponse:
        """
        Generate a response from the AI model.

        Args:
            messages: List of conversation messages.
            model: The model to use for generation.
            temperature: Controls randomness in the response.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            ModelResponse: The generated response with metadata.

        Raises:
            Exception: If the API call fails.
        """

    @abstractmethod
    async def validate_model(self, model: str) -> bool:
        """
        Validate if a model is available and can be used.

        Args:
            model: The model identifier to validate.

        Returns:
            bool: True if the model is valid and available.
        """

    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        Get a list of available models.

        Returns:
            List[str]: List of available model identifiers.
        """


if __name__ == "__main__":
    # Example usage (this won't run as it's an abstract class)
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello!")
    ]
