"""
Interview Assistant - Core Package

This package contains the refactored modular components for the Interview Assistant system.

Subpackages:
- core: Core infrastructure (logging, config, timing)
- transcription: Speech-to-text components
- llm: LLM and question detection
- audio: Audio processing and buffering
- server: WebSocket server components
- plugins: Plugin system (Phase 2)
"""

__version__ = "1.0.0"

# Re-export commonly used functions for convenience
from src.core.logger import get_logger, configure_logging
from src.core.config import get_config, reload_config
from src.core.timing import LatencyTracker, track_latency

__all__ = [
    "get_logger",
    "configure_logging",
    "get_config",
    "reload_config",
    "LatencyTracker",
    "track_latency",
]
