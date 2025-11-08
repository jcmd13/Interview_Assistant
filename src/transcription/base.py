"""
Transcription Plugin Interface

Defines the abstract interface that all transcription backends must implement.
Allows for pluggable speech-to-text engines (Whisper, AssemblyAI, Google Cloud, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import numpy as np

from src.core.plugins import PluginInterface, PluginType
from src.core.logger import get_logger

logger = get_logger("transcription.base")


@dataclass
class TranscriptionResult:
    """Result of a transcription operation"""

    text: str
    confidence: float  # 0.0 to 1.0
    language: str  # ISO 639-1 code (e.g., 'en')
    duration_ms: float  # Audio duration in milliseconds
    processing_time_ms: float  # Time taken to transcribe
    model_name: str  # Name of model used
    segments: Optional[List[Dict[str, Any]]] = None  # Optional segment-level details


class TranscriptionBackend(PluginInterface, ABC):
    """
    Abstract base class for transcription backends

    All transcription implementations must inherit from this class and implement
    the required abstract methods.

    Example:
        class WhisperTranscriber(TranscriptionBackend):
            @property
            def plugin_name(self) -> str:
                return "Whisper STT"

            @property
            def plugin_version(self) -> str:
                return "1.0.0"

            # ... implement other methods
    """

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Always returns PluginType.TRANSCRIPTION"""
        return PluginType.TRANSCRIPTION

    @abstractmethod
    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text

        Args:
            audio_data: Audio samples as numpy array (float32, normalized -1.0 to 1.0)
            sample_rate: Sample rate in Hz (default: 16000)
            language: Optional language code (e.g., 'en' for English)

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            TranscriptionError: If transcription fails
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
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        Returns:
            List of ISO 639-1 language codes
        """
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the backend

        Returns:
            Dictionary with metrics (avg latency, memory usage, etc.)
        """
        return {
            "plugin_name": self.plugin_name,
            "plugin_version": self.plugin_version,
            "model_name": getattr(self, '_current_model', 'unknown'),
            "status": "ready" if self.is_ready() else "not_ready",
        }

    def validate_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> bool:
        """
        Validate audio data before transcription

        Args:
            audio_data: Audio samples
            sample_rate: Sample rate in Hz

        Returns:
            True if audio is valid
        """
        # Check data type
        if not isinstance(audio_data, np.ndarray):
            logger.warning("Audio data is not numpy array", type=type(audio_data))
            return False

        # Check shape
        if audio_data.ndim != 1:
            logger.warning("Audio data must be 1D", shape=audio_data.shape)
            return False

        # Check value range (should be normalized)
        if np.max(np.abs(audio_data)) > 1.0:
            logger.warning(
                "Audio values exceed normalized range",
                max_value=float(np.max(np.abs(audio_data))),
            )
            # Note: this is a warning, not an error, as some backends can handle it

        # Check minimum length (at least 100ms at 16kHz = 1600 samples)
        min_samples = int(sample_rate * 0.1)  # 100ms
        if len(audio_data) < min_samples:
            logger.warning(
                "Audio too short",
                duration_ms=len(audio_data) / sample_rate * 1000,
                min_ms=100,
            )
            return False

        return True


class StreamingTranscriptionBackend(TranscriptionBackend, ABC):
    """
    Abstract base class for streaming transcription backends

    Allows for real-time transcription of audio chunks as they arrive.
    """

    @abstractmethod
    def start_stream(
        self,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> None:
        """
        Start a new transcription stream

        Args:
            sample_rate: Sample rate in Hz
            language: Optional language code
        """
        pass

    @abstractmethod
    def add_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """
        Add audio chunk to the stream

        Args:
            audio_chunk: Audio samples for this chunk

        Returns:
            Partial transcription if available, None otherwise
        """
        pass

    @abstractmethod
    def finish_stream(self) -> TranscriptionResult:
        """
        Finish the stream and return final transcription

        Returns:
            Final TranscriptionResult
        """
        pass

    def reset_stream(self) -> None:
        """Reset the current stream without finishing"""
        pass

    # Non-streaming methods should be implemented by subclass if needed
    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio data using streaming backend

        This default implementation uses the streaming interface internally.
        Subclasses can override for optimization.
        """
        self.start_stream(sample_rate=sample_rate, language=language)
        self.add_chunk(audio_data)
        return self.finish_stream()
