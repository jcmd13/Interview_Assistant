"""
Audio Processing Plugin Interface

Defines the abstract interface for audio processing plugins.
Allows for pluggable audio effects (noise cancellation, enhancement, compression, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

from src.core.plugins import PluginInterface, PluginType
from src.core.logger import get_logger

logger = get_logger("audio.base")


class AudioProcessType(str, Enum):
    """Types of audio processing"""
    PREPROCESSING = "preprocessing"  # Noise removal, normalization, etc.
    ENHANCEMENT = "enhancement"  # Voice enhancement, clarity, etc.
    ANALYSIS = "analysis"  # Feature extraction, quality metrics, etc.
    COMPRESSION = "compression"  # Audio compression algorithms
    CUSTOM = "custom"  # User-defined processing


@dataclass
class AudioMetrics:
    """Audio quality metrics"""

    duration_ms: float  # Audio duration
    sample_rate: int  # Sample rate in Hz
    bit_depth: int  # Bits per sample
    channels: int  # Number of channels
    rms_level: float  # RMS level (0.0 to 1.0)
    peak_level: float  # Peak level (0.0 to 1.0)
    snr_db: Optional[float] = None  # Signal-to-noise ratio in dB
    crest_factor: Optional[float] = None  # Peak to RMS ratio
    noise_level: Optional[float] = None  # Estimated noise level


class AudioProcessor(PluginInterface, ABC):
    """
    Abstract base class for audio processing plugins

    Audio processors can perform various operations on audio data such as:
    - Noise reduction
    - Audio enhancement
    - Feature extraction
    - Audio compression
    - Custom signal processing

    Example:
        class NoiseReducer(AudioProcessor):
            @property
            def plugin_name(self) -> str:
                return "Spectral Noise Reducer"

            @property
            def plugin_version(self) -> str:
                return "1.0.0"

            # ... implement other methods
    """

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Always returns PluginType.AUDIO"""
        return PluginType.AUDIO

    @property
    @abstractmethod
    def process_type(self) -> AudioProcessType:
        """Type of audio processing this plugin performs"""
        pass

    @abstractmethod
    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Process audio data

        Args:
            audio_data: Input audio samples (float32, -1.0 to 1.0)
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio samples (same format as input)

        Raises:
            AudioError: If processing fails
        """
        pass

    def analyze(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> AudioMetrics:
        """
        Analyze audio and return metrics

        Args:
            audio_data: Audio samples
            sample_rate: Sample rate in Hz

        Returns:
            AudioMetrics with analysis results
        """
        # Basic metrics calculation
        duration_ms = len(audio_data) / sample_rate * 1000
        rms_level = float(np.sqrt(np.mean(audio_data**2)))
        peak_level = float(np.max(np.abs(audio_data)))

        crest_factor = None
        if rms_level > 0:
            crest_factor = peak_level / rms_level

        return AudioMetrics(
            duration_ms=duration_ms,
            sample_rate=sample_rate,
            bit_depth=16,  # Assume 16-bit
            channels=1,  # Assume mono
            rms_level=rms_level,
            peak_level=peak_level,
            crest_factor=crest_factor,
        )

    def normalize(
        self,
        audio_data: np.ndarray,
        target_level: float = 0.95,
    ) -> np.ndarray:
        """
        Normalize audio to target level

        Args:
            audio_data: Audio samples
            target_level: Target peak level (0.0 to 1.0)

        Returns:
            Normalized audio
        """
        peak = np.max(np.abs(audio_data))
        if peak > 0:
            return (audio_data / peak) * target_level
        return audio_data

    def clip(
        self,
        audio_data: np.ndarray,
        threshold: float = 1.0,
    ) -> np.ndarray:
        """
        Clip audio to threshold

        Args:
            audio_data: Audio samples
            threshold: Clipping threshold

        Returns:
            Clipped audio
        """
        return np.clip(audio_data, -threshold, threshold)

    def gain(
        self,
        audio_data: np.ndarray,
        gain_db: float,
    ) -> np.ndarray:
        """
        Apply gain to audio

        Args:
            audio_data: Audio samples
            gain_db: Gain in decibels

        Returns:
            Audio with gain applied
        """
        gain_linear = 10 ** (gain_db / 20)
        return audio_data * gain_linear

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the processor

        Returns:
            Dictionary with metrics
        """
        return {
            "plugin_name": self.plugin_name,
            "plugin_version": self.plugin_version,
            "process_type": self.process_type.value,
            "status": "ready" if self.is_ready() else "not_ready",
        }


class ChainedAudioProcessor(AudioProcessor):
    """
    Process audio through a chain of processors

    Useful for combining multiple effects (e.g., noise reduction → enhancement → normalization)
    """

    def __init__(self, processors: Optional[List[AudioProcessor]] = None):
        """
        Initialize with optional list of processors

        Args:
            processors: List of AudioProcessor instances to chain
        """
        self.processors = processors or []
        self._plugin_name = "Chained Audio Processor"
        self._plugin_version = "1.0.0"

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def plugin_version(self) -> str:
        return self._plugin_version

    @property
    def process_type(self) -> AudioProcessType:
        return AudioProcessType.CUSTOM

    @property
    def dependencies(self) -> List[str]:
        return []

    def add_processor(self, processor: AudioProcessor) -> None:
        """Add a processor to the chain"""
        self.processors.append(processor)
        logger.info(
            "Processor added to chain",
            processor=processor.plugin_name,
            chain_length=len(self.processors),
        )

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize all processors in the chain"""
        for processor in self.processors:
            if not processor.is_ready():
                processor.initialize(config)
        logger.info("Chained processor initialized", chain_length=len(self.processors))

    def shutdown(self) -> None:
        """Shutdown all processors"""
        for processor in self.processors:
            processor.shutdown()

    def is_ready(self) -> bool:
        """Check if all processors are ready"""
        return all(p.is_ready() for p in self.processors)

    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """Process audio through all processors in order"""
        result = audio_data.copy()
        for processor in self.processors:
            result = processor.process(result, sample_rate=sample_rate)
        return result
