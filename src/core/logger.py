"""
Structured Logging Configuration

This module provides a structured logging system using structlog with JSON output,
timing metadata, and component-aware logging for the Interview Assistant.

Key Features:
- JSON-formatted log output for machine parsing
- Automatic timestamp and log level tracking
- Component-aware loggers (e.g., "transcription", "llm", "audio")
- Request ID correlation for tracking operations end-to-end
- Integration with Python's standard logging module
"""

import logging
import logging.config
import sys
from typing import Any, Dict, Optional
import uuid

import structlog
from structlog.types import EventDict, Processor


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_LOG_LEVEL = "INFO"  # Can be overridden per component


# ============================================================================
# Custom Processors
# ============================================================================

def add_request_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add a request_id to the event dict if not already present.

    This allows correlation of related log events across the pipeline.
    """
    if "request_id" not in event_dict:
        # Check if there's a request_id in the context
        event_dict["request_id"] = event_dict.get("_request_id", None)
    return event_dict


def add_component(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add the component name from the logger's context.

    Component names like "transcription.whisper", "llm.analyzer", etc.
    """
    # The component name is bound to the logger instance
    # This processor just ensures it's present
    return event_dict


# ============================================================================
# Logger Configuration
# ============================================================================

def configure_logging(
    log_level: str = DEFAULT_LOG_LEVEL,
    json_output: bool = True,
    pretty_print: bool = False
) -> None:
    """
    Configure the global structlog logging system.

    Args:
        log_level: Minimum log level to output (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON format; if False, use console format
        pretty_print: If True (and json_output=False), use pretty console output

    Example:
        >>> configure_logging(log_level="DEBUG", json_output=True)
        >>> logger = get_logger("transcription.whisper")
        >>> logger.info("model_loaded", model="base", device="cpu")
    """
    # Configure Python's standard logging to pass through to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Define the processor chain
    processors: list[Processor] = [
        # Add log level to the event dict
        structlog.stdlib.add_log_level,

        # Add logger name (component)
        structlog.stdlib.add_logger_name,

        # Add custom processors
        add_request_id,
        add_component,

        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),

        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),

        # Format exceptions nicely
        structlog.processors.format_exc_info,

        # Decode unicode
        structlog.processors.UnicodeDecoder(),
    ]

    # Choose final renderer
    if json_output:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    elif pretty_print:
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # Simple key=value output
        processors.append(structlog.processors.KeyValueRenderer(
            key_order=["timestamp", "level", "component", "event"]
        ))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ============================================================================
# Logger Factory
# ============================================================================

def get_logger(component: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a component-aware logger with optional initial context.

    Args:
        component: Component name (e.g., "transcription.whisper", "llm.analyzer")
        **initial_context: Additional context to bind to all log events

    Returns:
        A structlog logger instance bound to the component

    Example:
        >>> logger = get_logger("llm.analyzer", model="gpt-oss:120b-cloud")
        >>> logger.info("question_detected", question="What is REST?", confidence=0.95)

        Output:
        {
            "timestamp": "2025-10-28T10:30:45.123456Z",
            "level": "info",
            "logger": "llm.analyzer",
            "component": "llm.analyzer",
            "model": "gpt-oss:120b-cloud",
            "event": "question_detected",
            "question": "What is REST?",
            "confidence": 0.95
        }
    """
    logger = structlog.get_logger(component)

    # Bind the component and any initial context
    context = {"component": component}
    context.update(initial_context)

    return logger.bind(**context)


def get_logger_with_request_id(
    component: str,
    request_id: Optional[str] = None,
    **initial_context: Any
) -> structlog.stdlib.BoundLogger:
    """
    Get a logger with a request_id for correlation.

    Args:
        component: Component name
        request_id: Optional request ID (will generate one if not provided)
        **initial_context: Additional context to bind

    Returns:
        A logger with request_id bound for correlation

    Example:
        >>> logger = get_logger_with_request_id("audio.capture")
        >>> logger.info("audio_chunk_received", size_bytes=3200)
        >>> # Later in the pipeline
        >>> logger.info("transcription_complete", text="Hello world")
        # Both events will have the same request_id
    """
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]  # Short ID for readability

    context = {"request_id": request_id, "_request_id": request_id}
    context.update(initial_context)

    return get_logger(component, **context)


# ============================================================================
# Convenience Functions
# ============================================================================

def set_log_level(level: str) -> None:
    """
    Change the global log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR)

    Example:
        >>> set_log_level("DEBUG")  # Show all debug messages
    """
    logging.getLogger().setLevel(getattr(logging, level.upper()))


def enable_debug_logging() -> None:
    """Enable DEBUG level logging."""
    set_log_level("DEBUG")


def disable_debug_logging() -> None:
    """Disable DEBUG level logging (set to INFO)."""
    set_log_level("INFO")


# ============================================================================
# Initialization
# ============================================================================

# Auto-configure with sensible defaults on import
# This can be overridden by calling configure_logging() explicitly
configure_logging(
    log_level=DEFAULT_LOG_LEVEL,
    json_output=True,
    pretty_print=False
)
