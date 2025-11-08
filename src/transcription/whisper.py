"""
Faster-Whisper Transcription Plugin Implementation

Implements speech-to-text using OpenAI's Whisper model via faster-whisper backend.
Supports model switching, streaming transcription, and language detection.
"""

import time
from typing import Optional, Dict, Any, List
import numpy as np

from src.transcription.base import (
    TranscriptionBackend,
    StreamingTranscriptionBackend,
    TranscriptionResult,
)
from src.core.plugins import PluginType
from src.core.logger import get_logger

logger = get_logger("transcription.whisper")


class WhisperTranscriber(TranscriptionBackend):
    """
    Faster-Whisper transcription plugin for batch transcription.

    Uses the faster-whisper library which provides CTranslate2 optimization
    for faster inference compared to the standard OpenAI implementation.
    """

    def __init__(self):
        """Initialize the Whisper transcriber"""
        self._model = None
        self._current_model = None
        self._available_models = ["tiny", "base", "small", "medium", "large"]
        self._is_ready = False

    @property
    def plugin_name(self) -> str:
        """Plugin name"""
        return "Faster-Whisper Transcriber"

    @property
    def plugin_version(self) -> str:
        """Plugin version"""
        return "1.0.0"

    @property
    def plugin_type(self) -> PluginType:
        """Plugin type"""
        return PluginType.TRANSCRIPTION

    @property
    def dependencies(self) -> List[str]:
        """Required package dependencies"""
        return ["faster-whisper"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the Whisper model

        Args:
            config: Configuration dict with keys:
                - model_name: Model size (tiny, base, small, medium, large)
                - compute_type: Computation type (int8, float16, float32)
                - force_lang: Optional language code to skip detection
        """
        try:
            from faster_whisper import WhisperModel

            config = config or {}
            model_name = config.get("model_name", "base")
            compute_type = config.get("compute_type", "int8")
            self._force_lang = config.get("force_lang")

            logger.info(
                "Loading Whisper model",
                model=model_name,
                compute_type=compute_type,
            )

            # Load model
            self._model = WhisperModel(
                model_name,
                compute_type=compute_type,
                device="auto",
            )
            self._current_model = model_name
            self._is_ready = True

            logger.info(
                "Whisper model loaded",
                model=model_name,
                compute_type=compute_type,
            )

        except ImportError:
            logger.error(
                "faster-whisper not installed",
                help="pip install faster-whisper",
            )
            self._is_ready = False
        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e))
            self._is_ready = False

    def shutdown(self) -> None:
        """Cleanup model resources"""
        if self._model:
            try:
                del self._model
                self._model = None
                self._is_ready = False
                logger.info("Whisper model unloaded")
            except Exception as e:
                logger.error("Error during shutdown", error=str(e))

    def is_ready(self) -> bool:
        """Check if model is ready for transcription"""
        return self._is_ready and self._model is not None

    def set_model(self, model_name: str) -> bool:
        """
        Switch to a different model

        Args:
            model_name: Model size (tiny, base, small, medium, large)

        Returns:
            True if model switched successfully
        """
        if model_name == self._current_model:
            return True

        if model_name not in self._available_models:
            logger.error(
                "Invalid model name",
                model=model_name,
                available=self._available_models,
            )
            return False

        try:
            logger.info("Switching model", from_model=self._current_model, to_model=model_name)
            self.shutdown()
            self.initialize({"model_name": model_name})
            return self.is_ready()
        except Exception as e:
            logger.error("Failed to switch model", error=str(e))
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return self._available_models.copy()

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        Returns:
            List of ISO 639-1 language codes
        """
        # Whisper supports 99+ languages, returning common ones
        return [
            "en",  # English
            "es",  # Spanish
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "nl",  # Dutch
            "pl",  # Polish
            "ru",  # Russian
            "ja",  # Japanese
            "ko",  # Korean
            "zh",  # Chinese
            "ar",  # Arabic
            "hi",  # Hindi
        ]

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
        if not self.is_ready():
            from src.core.errors import TranscriptionError

            raise TranscriptionError("Whisper model not ready")

        start_time = time.time()

        try:
            # Use forced language if configured, otherwise auto-detect
            lang = self._force_lang or language

            logger.info(
                "Starting transcription",
                audio_duration_ms=len(audio_data) / sample_rate * 1000,
                language=lang,
                model=self._current_model,
            )

            # Perform transcription
            segments, info = self._model.transcribe(
                audio_data,
                language=lang,
                beam_size=5,
            )

            # Collect segments
            text = ""
            segment_list = []
            for segment in segments:
                text += segment.text + " "
                segment_list.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "confidence": segment.confidence if hasattr(segment, "confidence") else 0.9,
                    }
                )

            processing_time_ms = (time.time() - start_time) * 1000
            duration_ms = len(audio_data) / sample_rate * 1000

            # Estimate confidence from the segments
            confidence = (
                sum(s.get("confidence", 0.9) for s in segment_list) / len(segment_list)
                if segment_list
                else 0.9
            )

            logger.info(
                "Transcription complete",
                duration_ms=duration_ms,
                processing_time_ms=processing_time_ms,
                text_length=len(text.strip()),
                segments=len(segment_list),
                detected_language=info.language,
                model=self._current_model,
            )

            return TranscriptionResult(
                text=text.strip(),
                confidence=float(confidence),
                language=info.language or lang or "en",
                duration_ms=duration_ms,
                processing_time_ms=processing_time_ms,
                model_name=self._current_model,
                segments=segment_list,
            )

        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            from src.core.errors import TranscriptionError

            raise TranscriptionError(f"Whisper transcription failed: {str(e)}")


class StreamingWhisperTranscriber(StreamingTranscriptionBackend):
    """
    Streaming transcription using Whisper with chunked processing.

    Processes audio in chunks and returns partial results as they become available.
    Useful for real-time transcription with low latency.
    """

    def __init__(self):
        """Initialize streaming transcriber"""
        self._base_transcriber = WhisperTranscriber()
        self._audio_buffer = np.array([], dtype=np.float32)
        self._stream_active = False
        self._sample_rate = 16000
        self._language = None
        self._chunk_size = 16000 * 2  # 2 seconds at 16kHz

    @property
    def plugin_name(self) -> str:
        """Plugin name"""
        return "Streaming Whisper Transcriber"

    @property
    def plugin_version(self) -> str:
        """Plugin version"""
        return "1.0.0"

    @property
    def plugin_type(self) -> PluginType:
        """Plugin type"""
        return PluginType.TRANSCRIPTION

    @property
    def dependencies(self) -> List[str]:
        """Required dependencies"""
        return ["faster-whisper", "numpy"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize streaming transcriber"""
        self._base_transcriber.initialize(config)

    def shutdown(self) -> None:
        """Shutdown transcriber"""
        self._base_transcriber.shutdown()

    def is_ready(self) -> bool:
        """Check if ready for streaming"""
        return self._base_transcriber.is_ready()

    def set_model(self, model_name: str) -> bool:
        """Switch to different model"""
        return self._base_transcriber.set_model(model_name)

    def get_available_models(self) -> List[str]:
        """Get available models"""
        return self._base_transcriber.get_available_models()

    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return self._base_transcriber.get_supported_languages()

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
        self._audio_buffer = np.array([], dtype=np.float32)
        self._stream_active = True
        self._sample_rate = sample_rate
        self._language = language

        logger.info(
            "Stream started",
            sample_rate=sample_rate,
            language=language,
        )

    def add_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """
        Add audio chunk to stream

        Args:
            audio_chunk: Audio samples for this chunk

        Returns:
            Partial transcription if available, None otherwise
        """
        if not self._stream_active:
            logger.warning("Attempting to add chunk to inactive stream")
            return None

        # Append to buffer
        self._audio_buffer = np.concatenate([self._audio_buffer, audio_chunk])

        # Process if we have enough data (2 second chunks)
        if len(self._audio_buffer) >= self._chunk_size:
            # Process and return partial result
            try:
                result = self._base_transcriber.transcribe(
                    self._audio_buffer[: self._chunk_size],
                    sample_rate=self._sample_rate,
                    language=self._language,
                )
                # Keep overlap for context
                self._audio_buffer = self._audio_buffer[self._chunk_size // 2 :]
                return result.text
            except Exception as e:
                logger.error("Error processing stream chunk", error=str(e))
                return None

        return None

    def finish_stream(self) -> TranscriptionResult:
        """
        Finish stream and return final transcription

        Returns:
            Final TranscriptionResult
        """
        if not self._stream_active:
            logger.warning("Finishing inactive stream")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=self._language or "en",
                duration_ms=0.0,
                processing_time_ms=0.0,
                model_name=self._base_transcriber._current_model or "unknown",
            )

        try:
            # Process remaining audio
            if len(self._audio_buffer) > 0:
                result = self._base_transcriber.transcribe(
                    self._audio_buffer,
                    sample_rate=self._sample_rate,
                    language=self._language,
                )
            else:
                result = TranscriptionResult(
                    text="",
                    confidence=0.0,
                    language=self._language or "en",
                    duration_ms=0.0,
                    processing_time_ms=0.0,
                    model_name=self._base_transcriber._current_model or "unknown",
                )

            logger.info(
                "Stream finished",
                text_length=len(result.text),
                duration_ms=result.duration_ms,
            )

            self._stream_active = False
            self._audio_buffer = np.array([], dtype=np.float32)
            return result

        except Exception as e:
            logger.error("Error finishing stream", error=str(e))
            self._stream_active = False
            from src.core.errors import TranscriptionError

            raise TranscriptionError(f"Failed to finish stream: {str(e)}")

    def reset_stream(self) -> None:
        """Reset stream without finishing"""
        self._audio_buffer = np.array([], dtype=np.float32)
        self._stream_active = False
        logger.info("Stream reset")
