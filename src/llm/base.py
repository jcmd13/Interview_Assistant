"""
LLM (Language Model) Plugin Interface

Defines the abstract interface that all LLM backends must implement.
Allows for pluggable language models (Ollama, OpenAI, Anthropic, local models, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from src.core.plugins import PluginInterface, PluginType
from src.core.logger import get_logger

logger = get_logger("llm.base")


class Role(str, Enum):
    """Chat message role"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """A message in a conversation"""

    role: Role
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM"""

    text: str
    model: str
    tokens_used: Optional[int] = None  # Total tokens (input + output)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    processing_time_ms: float = 0.0
    stop_reason: str = "stop"  # "stop", "length", "error", etc.


class LLMBackend(PluginInterface, ABC):
    """
    Abstract base class for LLM backends

    All language model implementations must inherit from this class and implement
    the required abstract methods.

    Example:
        class OllamaLLM(LLMBackend):
            @property
            def plugin_name(self) -> str:
                return "Ollama"

            @property
            def plugin_version(self) -> str:
                return "1.0.0"

            # ... implement other methods
    """

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Always returns PluginType.LLM"""
        return PluginType.LLM

    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM

        Args:
            messages: Conversation history (list of ChatMessage objects)
            temperature: Sampling temperature (0.0 to 2.0, higher = more random)
            max_tokens: Maximum tokens in response (None = default)

        Returns:
            LLMResponse with generated text

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def set_model(self, model_name: str) -> bool:
        """
        Switch to a different model

        Args:
            model_name: Name of model to load

        Returns:
            True if model loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models

        Returns:
            List of available model names
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM service is available and responding

        Returns:
            True if service is available, False otherwise
        """
        pass

    def extract_json(
        self,
        messages: List[ChatMessage],
        schema: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate and extract JSON response from the LLM

        Args:
            messages: Conversation history
            schema: Optional JSON schema to validate against
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON dictionary

        Raises:
            LLMError: If JSON extraction fails
        """
        response = self.chat(messages, max_tokens=max_tokens)

        import json

        try:
            # Try to extract JSON from the response
            json_start = response.text.find("{")
            json_end = response.text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response.text[json_start:json_end]
                data = json.loads(json_str)

                # Validate schema if provided
                if schema:
                    # Basic schema validation (would use jsonschema in production)
                    for key in schema.get("required", []):
                        if key not in data:
                            raise ValueError(f"Missing required field: {key}")

                return data
            else:
                raise ValueError("No JSON found in response")

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from LLM response", error=str(e))
            raise

    def list_questions(
        self,
        text: str,
        max_questions: int = 10,
    ) -> List[str]:
        """
        Extract questions from text using the LLM

        Args:
            text: Text to analyze
            max_questions: Maximum number of questions to extract

        Returns:
            List of extracted questions
        """
        system_msg = (
            f"Extract up to {max_questions} questions from the text. "
            "Return as JSON array: {\"questions\": [...]}"
        )

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            result = self.extract_json(messages)
            return result.get("questions", [])[:max_questions]
        except Exception as e:
            logger.error("Failed to extract questions", error=str(e))
            return []

    def classify_text(
        self,
        text: str,
        categories: List[str],
    ) -> Optional[str]:
        """
        Classify text into one of the provided categories

        Args:
            text: Text to classify
            categories: List of categories to choose from

        Returns:
            Predicted category, or None if classification fails
        """
        categories_str = ", ".join(categories)
        system_msg = (
            f"Classify the text into one of these categories: {categories_str}. "
            "Return JSON: {\"category\": \"<category>\"}"
        )

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            result = self.extract_json(messages)
            category = result.get("category")
            if category in categories:
                return category
            return None
        except Exception as e:
            logger.error("Failed to classify text", error=str(e))
            return None

    def summarize(
        self,
        text: str,
        max_length: int = 100,
    ) -> str:
        """
        Summarize text

        Args:
            text: Text to summarize
            max_length: Maximum length of summary

        Returns:
            Summarized text
        """
        system_msg = f"Summarize the text in {max_length} characters or less."

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            response = self.chat(messages, max_tokens=max_length // 4)
            return response.text
        except Exception as e:
            logger.error("Failed to summarize text", error=str(e))
            return ""

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the backend

        Returns:
            Dictionary with metrics (avg latency, tokens, etc.)
        """
        return {
            "plugin_name": self.plugin_name,
            "plugin_version": self.plugin_version,
            "model_name": getattr(self, "_current_model", "unknown"),
            "status": "available" if self.is_available() else "unavailable",
        }
