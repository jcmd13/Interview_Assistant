"""
Audio Package

This package contains audio processing and device management components.

Components:
- device_manager: Audio device enumeration and switching (hot-swapping)
- buffer: Audio buffer management for rolling windows
- processor: Audio preprocessing and quality enhancement (Phase 3)
"""

from .device_manager import AudioDeviceManager, AudioDevice, get_device_manager

__all__ = [
    "AudioDeviceManager",
    "AudioDevice",
    "get_device_manager",
]
