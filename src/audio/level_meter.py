"""
Audio Level Meter
Monitors audio input levels for VU meter display
"""

import numpy as np
from typing import Dict, Any, Optional
from collections import deque
from datetime import datetime


class AudioLevelMeter:
    """Monitors and reports audio input levels"""

    def __init__(self, history_size: int = 60, update_rate: float = 0.1):
        """
        Initialize audio level meter

        Args:
            history_size: Number of samples to keep in history
            update_rate: Seconds between updates
        """
        self.history_size = history_size
        self.update_rate = update_rate
        self.history: deque = deque(maxlen=history_size)
        self.peak_level = 0.0
        self.rms_level = 0.0
        self.last_update = datetime.now()
        self.is_clipping = False

    def process_audio(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Process audio frame and calculate levels

        Args:
            audio_data: Audio samples (numpy array)

        Returns:
            Dict with level information
        """
        if len(audio_data) == 0:
            return self.get_status()

        # Calculate RMS level (0.0 to 1.0)
        rms = np.sqrt(np.mean(audio_data ** 2))
        self.rms_level = float(rms)

        # Calculate peak level
        peak = np.max(np.abs(audio_data))
        self.peak_level = float(peak)

        # Check for clipping (level > 1.0)
        self.is_clipping = peak > 0.95

        # Add to history
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "rms": self.rms_level,
            "peak": self.peak_level,
            "clipping": self.is_clipping,
        })

        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        """Get current audio level status"""
        # Calculate average levels from history
        avg_rms = np.mean([h["rms"] for h in self.history]) if self.history else 0.0
        avg_peak = np.max([h["peak"] for h in self.history]) if self.history else 0.0

        # Convert to dB (20 * log10(level), with floor at -80dB)
        def to_db(level: float) -> float:
            if level < 0.00001:
                return -80.0
            return max(-80.0, 20.0 * np.log10(level))

        return {
            "rms_level": self.rms_level,
            "peak_level": self.peak_level,
            "rms_db": to_db(avg_rms),
            "peak_db": to_db(avg_peak),
            "is_clipping": self.is_clipping,
            "average_rms": float(avg_rms),
            "history_size": len(self.history),
        }

    def get_vu_display(self) -> str:
        """Get ASCII VU meter display"""
        db = max(-80.0, 20.0 * np.log10(max(0.00001, self.rms_level)))
        # Map -80dB to 0, 0dB to 20 (scale: 4 points per dB in useful range)
        meter_pos = max(0, min(20, int((db + 80) / 4)))
        meter_bar = "█" * meter_pos + "░" * (20 - meter_pos)
        clip_indicator = "🔴 CLIPPING" if self.is_clipping else "🟢 OK"
        return f"[{meter_bar}] {self.rms_level:.3f} {clip_indicator}"

    def reset_peak(self):
        """Reset peak level"""
        self.peak_level = 0.0


class StreamAudioLevelMonitor:
    """Monitors audio levels from incoming stream data"""

    def __init__(self):
        """Initialize stream monitor"""
        self.meter = AudioLevelMeter()
        self.total_samples = 0
        self.sample_rate = 16000

    def process_pcm_chunk(self, pcm_data: bytes) -> Dict[str, Any]:
        """
        Process PCM audio chunk (16-bit signed, mono)

        Args:
            pcm_data: Raw PCM bytes

        Returns:
            Level status dict
        """
        # Convert bytes to numpy array (16-bit signed, little-endian)
        audio_array = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32)

        # Normalize to -1.0 to 1.0 range
        if len(audio_array) > 0:
            audio_array = audio_array / 32768.0
            self.total_samples += len(audio_array)

        return self.meter.process_audio(audio_array)

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        status = self.meter.get_status()
        status["total_samples"] = self.total_samples
        status["duration_seconds"] = self.total_samples / self.sample_rate
        return status

    def get_vu_display(self) -> str:
        """Get ASCII VU meter display"""
        return self.meter.get_vu_display()
