"""
Ollama LLM Backend Plugin Implementation

Implements language model interface using Ollama local API.
Supports model switching, JSON extraction, and text analysis tasks.
Requires running Ollama service: `ollama serve`
"""

import json
import time
from typing import Optional, Dict, Any, List
import asyncio

from src.llm.base import (
    LLMBackend,
    ChatMessage,
    Role,
    LLMResponse,
)
from src.core.plugins import PluginType
from src.core.logger import get_logger

logger = get_logger("llm.ollama")


class OllamaLLM(LLMBackend):
    """
    Ollama language model backend for local LLM inference.

    Uses the Ollama Python client to communicate with a local Ollama service.
    All processing happens locally - no data sent to cloud services.
    """

    def __init__(self):
        """Initialize Ollama LLM backend"""
        self._client = None
        self._current_model = None
        self._available_models = []
        self._is_available = False
        self._base_url = "http://localhost:11434"

    @property
    def plugin_name(self) -> str:
        """Plugin name"""
        return "Ollama LLM Backend"

    @property
    def plugin_version(self) -> str:
        """Plugin version"""
        return "1.0.0"

    @property
    def plugin_type(self) -> PluginType:
        """Plugin type"""
        return PluginType.LLM

    @property
    def dependencies(self) -> List[str]:
        """Required package dependencies"""
        return ["ollama"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize Ollama backend

        Args:
            config: Configuration dict with keys:
                - base_url: Ollama API URL (default: http://localhost:11434)
                - default_model: Model to use by default
        """
        try:
            import ollama

            config = config or {}
            self._base_url = config.get("base_url", "http://localhost:11434")
            default_model = config.get("default_model")

            logger.info(
                "Initializing Ollama backend",
                base_url=self._base_url,
            )

            # Test connection and get available models
            try:
                response = ollama.list()
                if hasattr(response, "models"):
                    self._available_models = [m.model for m in response.models]
                else:
                    self._available_models = response.get("models", [])

                logger.info(
                    "Ollama connection established",
                    available_models=len(self._available_models),
                    models=self._available_models[:5],  # Log first 5 models
                )

                # Set default or first available model
                if default_model and default_model in self._available_models:
                    self._current_model = default_model
                elif self._available_models:
                    self._current_model = self._available_models[0]
                    logger.warning(
                        "Using first available model",
                        model=self._current_model,
                    )

                self._is_available = True

            except Exception as e:
                logger.error(
                    "Ollama connection failed",
                    error=str(e),
                    help="Make sure Ollama is running: 'ollama serve'",
                    base_url=self._base_url,
                )
                self._is_available = False

        except ImportError:
            logger.error(
                "ollama package not installed",
                help="pip install ollama",
            )
            self._is_available = False

    def shutdown(self) -> None:
        """Cleanup resources"""
        self._is_available = False
        logger.info("Ollama backend shutdown")

    def is_ready(self) -> bool:
        """Check if backend is ready"""
        return self._is_available and self._current_model is not None

    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        if not self._is_available:
            return False

        try:
            import ollama

            ollama.show(self._current_model)
            return True
        except Exception:
            return False

    def set_model(self, model_name: str) -> bool:
        """
        Switch to a different model

        Args:
            model_name: Name of model to use

        Returns:
            True if model set successfully
        """
        if model_name == self._current_model:
            return True

        if model_name not in self._available_models:
            logger.warning(
                "Model not in available list, attempting anyway",
                model=model_name,
                available=self._available_models[:5],
            )

        try:
            import ollama

            # Verify model exists by trying to show it
            ollama.show(model_name)

            logger.info(
                "Model switched",
                from_model=self._current_model,
                to_model=model_name,
            )

            self._current_model = model_name
            return True

        except Exception as e:
            logger.error("Failed to set model", error=str(e), model=model_name)
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not self._available_models:
            try:
                import ollama

                response = ollama.list()
                if hasattr(response, "models"):
                    self._available_models = [m.model for m in response.models]
                else:
                    self._available_models = response.get("models", [])
            except Exception as e:
                logger.error("Failed to list models", error=str(e))

        return self._available_models.copy()

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate response from language model

        Args:
            messages: Conversation history (list of ChatMessage)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLMResponse with generated text

        Raises:
            LLMError: If generation fails
        """
        if not self.is_ready():
            from src.core.errors import LLMError

            raise LLMError("Ollama LLM not ready")

        start_time = time.time()

        try:
            import ollama

            # Convert ChatMessage to ollama format
            formatted_messages = [
                {"role": message.role.value, "content": message.content}
                for message in messages
            ]

            logger.info(
                "Chat request",
                model=self._current_model,
                message_count=len(formatted_messages),
                temperature=temperature,
            )

            # Make API call
            response = ollama.chat(
                model=self._current_model,
                messages=formatted_messages,
                temperature=temperature,
                stream=False,
            )

            processing_time_ms = (time.time() - start_time) * 1000

            # Extract response content
            if isinstance(response, dict):
                text = response.get("message", {}).get("content", "")
                stop_reason = response.get("done_reason", "stop")
            else:
                # Handle response object
                text = response.message.content if hasattr(response, "message") else str(response)
                stop_reason = "stop"

            logger.info(
                "Chat response received",
                model=self._current_model,
                response_length=len(text),
                processing_time_ms=processing_time_ms,
                stop_reason=stop_reason,
            )

            return LLMResponse(
                text=text,
                model=self._current_model,
                processing_time_ms=processing_time_ms,
                stop_reason=stop_reason,
            )

        except Exception as e:
            logger.error("Chat generation failed", error=str(e))
            from src.core.errors import LLMError

            raise LLMError(f"Ollama chat failed: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "plugin_name": self.plugin_name,
            "plugin_version": self.plugin_version,
            "model_name": self._current_model,
            "status": "available" if self.is_available() else "unavailable",
            "available_models": len(self._available_models),
        }


class OllamaAnalyzer:
    """
    High-level analyzer for Ollama-powered question detection and analysis.

    Provides specialized methods for extracting questions, classifying text,
    and generating responses with context awareness.
    """

    def __init__(self, llm_backend: Optional[OllamaLLM] = None):
        """
        Initialize analyzer

        Args:
            llm_backend: OllamaLLM instance (creates new if not provided)
        """
        self.llm = llm_backend or OllamaLLM()
        if not self.llm.is_ready():
            self.llm.initialize()

    def extract_questions(self, text: str, max_questions: int = 5) -> List[str]:
        """
        Extract questions from text

        Args:
            text: Text to analyze
            max_questions: Maximum number of questions to extract

        Returns:
            List of extracted questions
        """
        system_msg = (
            f"Extract up to {max_questions} questions or topics needing clarification "
            "from the provided text. Return ONLY a JSON array of question strings. "
            "Examples: ['What does X mean?', 'How do we handle Y?']"
        )

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            result = self.llm.extract_json(messages)
            questions = result.get("questions", [])
            if not isinstance(questions, list):
                questions = [str(questions)]
            return questions[:max_questions]
        except Exception as e:
            logger.error("Failed to extract questions", error=str(e))
            return []

    def classify_content(self, text: str, categories: List[str]) -> Optional[str]:
        """
        Classify text into one of provided categories

        Args:
            text: Text to classify
            categories: List of possible categories

        Returns:
            Predicted category or None if classification fails
        """
        categories_str = ", ".join(categories)
        system_msg = (
            f"Classify the given text into exactly one of these categories: {categories_str}. "
            "Return ONLY valid JSON: {{\"category\": \"<category>\"}}"
        )

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            result = self.llm.extract_json(messages)
            category = result.get("category")
            if category in categories:
                return category
            return None
        except Exception as e:
            logger.error("Failed to classify content", error=str(e))
            return None

    def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        tone: str = "professional",
    ) -> str:
        """
        Generate an answer to a question

        Args:
            question: The question to answer
            context: Optional context for the answer
            tone: Tone of response (professional, casual, technical, simple)

        Returns:
            Generated answer
        """
        tone_guidance = {
            "professional": "Use a professional, concise tone.",
            "casual": "Use a friendly, conversational tone.",
            "technical": "Use technical terminology with depth.",
            "simple": "Explain simply without jargon.",
        }

        system_msg = f"""You are a helpful assistant answering questions during an interview.
{tone_guidance.get(tone, tone_guidance['professional'])}
Answer concisely but comprehensively. Keep answers under 200 words."""

        user_content = question
        if context:
            user_content = f"Context: {context}\n\nQuestion: {question}"

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=user_content),
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3)
            return response.text
        except Exception as e:
            logger.error("Failed to generate answer", error=str(e))
            return f"Unable to generate answer: {str(e)}"

    def summarize(self, text: str, max_length: int = 150) -> str:
        """
        Summarize text

        Args:
            text: Text to summarize
            max_length: Maximum length of summary

        Returns:
            Summary text
        """
        system_msg = f"Summarize the given text in {max_length} characters or less. Be concise."

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            response = self.llm.chat(messages, temperature=0.2)
            return response.text
        except Exception as e:
            logger.error("Failed to summarize", error=str(e))
            return ""

    def detect_topics(self, text: str) -> List[str]:
        """
        Detect topics/subjects in text

        Args:
            text: Text to analyze

        Returns:
            List of detected topics
        """
        system_msg = (
            "Extract the main topics or subjects discussed in the text. "
            "Return ONLY a JSON array of topic strings. "
            'Example: ["authentication", "deployment", "monitoring"]'
        )

        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_msg),
            ChatMessage(role=Role.USER, content=text),
        ]

        try:
            result = self.llm.extract_json(messages)
            topics = result.get("topics", [])
            if not isinstance(topics, list):
                topics = [str(topics)]
            return topics
        except Exception as e:
            logger.error("Failed to detect topics", error=str(e))
            return []
