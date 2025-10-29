"""
Core Infrastructure Package

This package contains shared infrastructure components used throughout
the Interview Assistant application.

Components:
- logger: Structured logging system
- config: Configuration management
- timing: Performance monitoring and telemetry
"""

__all__ = [
    "get_logger",
    "configure_logging",
    "get_config",
    "reload_config",
    "LatencyTracker",
    "track_latency",
]

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "get_logger" or name == "configure_logging":
        from .logger import get_logger, configure_logging
        return get_logger if name == "get_logger" else configure_logging
    elif name == "get_config" or name == "reload_config":
        from .config import get_config, reload_config
        return get_config if name == "get_config" else reload_config
    elif name == "LatencyTracker" or name == "track_latency":
        from .timing import LatencyTracker, track_latency
        return LatencyTracker if name == "LatencyTracker" else track_latency
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
