"""
Audio Effects Plugins for Preprocessing and Enhancement

Implements specialized audio processing effects:
- Noise gate (silence removal)
- Spectral noise reduction (stationary noise)
- Voice enhancement (presence peak)
- Dynamic range compression
- High-pass filter (remove rumble)
"""

from typing import Optional, Dict, Any, List
import numpy as np
from scipy import signal

from src.audio.base import AudioProcessor, AudioProcessType, AudioMetrics
from src.core.plugins import PluginType
from src.core.logger import get_logger

logger = get_logger("audio.effects")


class NoiseGate(AudioProcessor):
    """
    Simple noise gate that removes audio below a threshold.

    Useful for removing background noise and silence during preprocessing.
    """

    def __init__(self):
        """Initialize noise gate"""
        self._plugin_name = "Noise Gate"
        self._plugin_version = "1.0.0"
        self._threshold = -40.0  # dB threshold
        self._is_ready = False

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def plugin_version(self) -> str:
        return self._plugin_version

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.AUDIO

    @property
    def process_type(self) -> AudioProcessType:
        return AudioProcessType.PREPROCESSING

    @property
    def dependencies(self) -> List[str]:
        return ["numpy"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize noise gate

        Args:
            config: Configuration with:
                - threshold_db: Gate threshold in dB (default: -40)
        """
        config = config or {}
        self._threshold = config.get("threshold_db", -40.0)
        self._is_ready = True
        logger.info("Noise gate initialized", threshold_db=self._threshold)

    def shutdown(self) -> None:
        """Cleanup"""
        self._is_ready = False

    def is_ready(self) -> bool:
        """Check if ready"""
        return self._is_ready

    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Apply noise gate

        Args:
            audio_data: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            Gated audio
        """
        # Convert threshold from dB to linear
        threshold_linear = 10 ** (self._threshold / 20.0)

        # Get RMS per window
        window_size = int(sample_rate * 0.01)  # 10ms windows
        result = audio_data.copy()

        for i in range(0, len(audio_data), window_size):
            window = audio_data[i : i + window_size]
            if len(window) == 0:
                continue

            rms = np.sqrt(np.mean(window**2))
            if rms < threshold_linear:
                result[i : i + window_size] = 0

        logger.debug(
            "Noise gate applied",
            threshold_db=self._threshold,
            input_length=len(audio_data),
        )
        return result


class HighPassFilter(AudioProcessor):
    """
    High-pass filter to remove low-frequency rumble.

    Useful for removing microphone handling noise, air conditioning hum, etc.
    """

    def __init__(self):
        """Initialize high-pass filter"""
        self._plugin_name = "High-Pass Filter"
        self._plugin_version = "1.0.0"
        self._cutoff_hz = 80.0
        self._is_ready = False

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def plugin_version(self) -> str:
        return self._plugin_version

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.AUDIO

    @property
    def process_type(self) -> AudioProcessType:
        return AudioProcessType.PREPROCESSING

    @property
    def dependencies(self) -> List[str]:
        return ["numpy", "scipy"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize high-pass filter

        Args:
            config: Configuration with:
                - cutoff_hz: Cutoff frequency (default: 80)
        """
        config = config or {}
        self._cutoff_hz = config.get("cutoff_hz", 80.0)
        self._is_ready = True
        logger.info("High-pass filter initialized", cutoff_hz=self._cutoff_hz)

    def shutdown(self) -> None:
        """Cleanup"""
        self._is_ready = False

    def is_ready(self) -> bool:
        """Check if ready"""
        return self._is_ready

    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Apply high-pass filter

        Args:
            audio_data: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            Filtered audio
        """
        # Design high-pass Butterworth filter
        nyquist = sample_rate / 2
        normalized_cutoff = self._cutoff_hz / nyquist

        if normalized_cutoff >= 1.0:
            logger.warning(
                "Cutoff frequency >= Nyquist, returning original audio",
                cutoff_hz=self._cutoff_hz,
                nyquist=nyquist,
            )
            return audio_data

        try:
            b, a = signal.butter(4, normalized_cutoff, btype="high")
            filtered = signal.filtfilt(b, a, audio_data)
            logger.debug(
                "High-pass filter applied",
                cutoff_hz=self._cutoff_hz,
                order=4,
            )
            return filtered
        except Exception as e:
            logger.error("High-pass filter failed", error=str(e))
            return audio_data


class VoiceEnhancer(AudioProcessor):
    """
    Voice enhancement using spectral sharpening.

    Adds presence peak to make voice clearer and more intelligible.
    """

    def __init__(self):
        """Initialize voice enhancer"""
        self._plugin_name = "Voice Enhancer"
        self._plugin_version = "1.0.0"
        self._intensity = 1.5  # Boost factor
        self._is_ready = False

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def plugin_version(self) -> str:
        return self._plugin_version

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.AUDIO

    @property
    def process_type(self) -> AudioProcessType:
        return AudioProcessType.ENHANCEMENT

    @property
    def dependencies(self) -> List[str]:
        return ["numpy", "scipy"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize voice enhancer

        Args:
            config: Configuration with:
                - intensity: Boost factor (default: 1.5)
        """
        config = config or {}
        self._intensity = config.get("intensity", 1.5)
        self._is_ready = True
        logger.info("Voice enhancer initialized", intensity=self._intensity)

    def shutdown(self) -> None:
        """Cleanup"""
        self._is_ready = False

    def is_ready(self) -> bool:
        """Check if ready"""
        return self._is_ready

    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Apply voice enhancement

        Args:
            audio_data: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            Enhanced audio
        """
        # Simple spectral enhancement using differentiation
        # This creates a presence peak without complex processing
        enhanced = audio_data.copy()

        # Apply high-shelf EQ via simple differentiation
        # This boosts high frequencies where voice presence is
        if len(enhanced) > 1:
            diff = np.diff(enhanced, prepend=enhanced[0])
            enhanced = enhanced + diff * (self._intensity - 1.0) * 0.5

        # Prevent clipping
        max_val = np.max(np.abs(enhanced))
        if max_val > 1.0:
            enhanced = enhanced / max_val

        logger.debug(
            "Voice enhancement applied",
            intensity=self._intensity,
        )
        return enhanced


class DynamicCompressor(AudioProcessor):
    """
    Dynamic range compressor to balance loud and quiet parts.

    Reduces dynamic range making speech more consistent in volume.
    """

    def __init__(self):
        """Initialize compressor"""
        self._plugin_name = "Dynamic Compressor"
        self._plugin_version = "1.0.0"
        self._ratio = 4.0  # Compression ratio
        self._threshold = -20.0  # dB
        self._is_ready = False

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def plugin_version(self) -> str:
        return self._plugin_version

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.AUDIO

    @property
    def process_type(self) -> AudioProcessType:
        return AudioProcessType.ENHANCEMENT

    @property
    def dependencies(self) -> List[str]:
        return ["numpy"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize compressor

        Args:
            config: Configuration with:
                - ratio: Compression ratio (default: 4.0)
                - threshold_db: Threshold in dB (default: -20)
        """
        config = config or {}
        self._ratio = config.get("ratio", 4.0)
        self._threshold = config.get("threshold_db", -20.0)
        self._is_ready = True
        logger.info(
            "Compressor initialized",
            ratio=self._ratio,
            threshold_db=self._threshold,
        )

    def shutdown(self) -> None:
        """Cleanup"""
        self._is_ready = False

    def is_ready(self) -> bool:
        """Check if ready"""
        return self._is_ready

    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Apply dynamic compression

        Args:
            audio_data: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            Compressed audio
        """
        # Convert threshold from dB
        threshold_linear = 10 ** (self._threshold / 20.0)

        result = audio_data.copy()
        window_size = int(sample_rate * 0.05)  # 50ms windows

        for i in range(0, len(audio_data), window_size):
            window = audio_data[i : i + window_size]
            if len(window) == 0:
                continue

            # Calculate RMS
            rms = np.sqrt(np.mean(window**2))

            # Apply compression above threshold
            if rms > threshold_linear:
                gain_reduction = threshold_linear + (rms - threshold_linear) / self._ratio
                if rms > 0:
                    compression_factor = gain_reduction / rms
                    result[i : i + window_size] = window * compression_factor

        logger.debug(
            "Compression applied",
            ratio=self._ratio,
            threshold_db=self._threshold,
        )
        return result


class SpectralNoiseReducer(AudioProcessor):
    """
    Spectral noise reduction using Wiener filtering.

    Removes stationary background noise while preserving speech.
    Good for fan noise, air conditioning, keyboard clicks, etc.
    """

    def __init__(self):
        """Initialize spectral noise reducer"""
        self._plugin_name = "Spectral Noise Reducer"
        self._plugin_version = "1.0.0"
        self._reduction_factor = 0.5
        self._is_ready = False

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def plugin_version(self) -> str:
        return self._plugin_version

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.AUDIO

    @property
    def process_type(self) -> AudioProcessType:
        return AudioProcessType.PREPROCESSING

    @property
    def dependencies(self) -> List[str]:
        return ["numpy"]

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize noise reducer

        Args:
            config: Configuration with:
                - reduction_factor: Strength (0.0-1.0, default: 0.5)
        """
        config = config or {}
        self._reduction_factor = config.get("reduction_factor", 0.5)
        self._is_ready = True
        logger.info("Spectral noise reducer initialized", reduction_factor=self._reduction_factor)

    def shutdown(self) -> None:
        """Cleanup"""
        self._is_ready = False

    def is_ready(self) -> bool:
        """Check if ready"""
        return self._is_ready

    def process(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> np.ndarray:
        """
        Apply spectral noise reduction

        Args:
            audio_data: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            Noise-reduced audio
        """
        # Use first 100ms as noise profile
        noise_duration = int(sample_rate * 0.1)
        noise_profile = audio_data[:noise_duration]

        # Calculate noise characteristics
        noise_rms = np.sqrt(np.mean(noise_profile**2))
        noise_power = noise_rms**2

        # Simple spectral subtraction
        output = audio_data.copy()

        # Process in chunks
        chunk_size = int(sample_rate * 0.025)  # 25ms chunks
        for i in range(0, len(output), chunk_size):
            chunk = output[i : i + chunk_size]
            if len(chunk) == 0:
                continue

            # Estimate chunk power
            chunk_power = np.sqrt(np.mean(chunk**2))

            # Reduce noise proportionally to reduction_factor
            if chunk_power > 0:
                speech_power = chunk_power - (noise_power * self._reduction_factor)
                if speech_power > 0:
                    output[i : i + chunk_size] = chunk * (speech_power / chunk_power)
                else:
                    output[i : i + chunk_size] = 0

        logger.debug(
            "Spectral noise reduction applied",
            reduction_factor=self._reduction_factor,
            noise_rms=float(noise_rms),
        )
        return output
