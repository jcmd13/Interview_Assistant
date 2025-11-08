"""
Error Handling & Input Validation Framework

Provides:
- Custom exception hierarchy
- Input validation decorators
- Error recovery strategies
- User-friendly error messages
- Logging integration
"""

from typing import Any, Callable, Optional, Type, TypeVar, Union
from functools import wraps
import traceback
from enum import Enum

from src.core.logger import get_logger

logger = get_logger("system.errors")

F = TypeVar('F', bound=Callable[..., Any])


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    INFO = "info"          # Informational, no action needed
    WARNING = "warning"    # Warning, user should be aware
    ERROR = "error"        # Error, operation failed
    CRITICAL = "critical"  # Critical, system may be unstable


class InterviewAssistantError(Exception):
    """Base exception for all Interview Assistant errors"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        Initialize error with structured information

        Args:
            message: Technical error message (for logs)
            severity: Error severity level
            user_message: User-friendly message (for UI)
            error_code: Machine-readable error code
            details: Additional context data
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.user_message = user_message or message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def log(self) -> None:
        """Log the error at appropriate level"""
        log_method = getattr(logger, self.severity.value)
        log_method(
            self.message,
            error_code=self.error_code,
            severity=self.severity.value,
            details=self.details,
        )

    def to_dict(self) -> dict:
        """Convert error to dict for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.user_message,
            "severity": self.severity.value,
            "details": self.details,
        }


# Audio Errors
class AudioError(InterviewAssistantError):
    """Base class for audio-related errors"""
    pass


class AudioDeviceError(AudioError):
    """Audio device not found or unavailable"""

    def __init__(self, device_name: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Audio device not found: {device_name}",
            severity=ErrorSeverity.ERROR,
            user_message=f"Cannot find audio device '{device_name}'. Check audio input settings.",
            error_code="AUDIO_DEVICE_NOT_FOUND",
            details=details or {"device": device_name},
        )


class AudioProcessingError(AudioError):
    """Error during audio processing"""

    def __init__(self, operation: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Error during audio {operation}",
            severity=ErrorSeverity.ERROR,
            user_message="Audio processing failed. Check audio device and try again.",
            error_code="AUDIO_PROCESSING_FAILED",
            details=details or {"operation": operation},
        )


# Transcription Errors
class TranscriptionError(InterviewAssistantError):
    """Base class for transcription errors"""
    pass


class ModelNotFoundError(TranscriptionError):
    """Requested model not available"""

    def __init__(self, model_name: str, model_type: str):
        super().__init__(
            message=f"{model_type} model '{model_name}' not found",
            severity=ErrorSeverity.ERROR,
            user_message=f"Model '{model_name}' is not installed. Install it first.",
            error_code="MODEL_NOT_FOUND",
            details={"model": model_name, "model_type": model_type},
        )


class TranscriptionTimeoutError(TranscriptionError):
    """Transcription took too long"""

    def __init__(self, timeout_ms: int):
        super().__init__(
            message=f"Transcription timed out after {timeout_ms}ms",
            severity=ErrorSeverity.ERROR,
            user_message="Transcription is taking too long. Try a smaller audio segment.",
            error_code="TRANSCRIPTION_TIMEOUT",
            details={"timeout_ms": timeout_ms},
        )


# LLM Errors
class LLMError(InterviewAssistantError):
    """Base class for LLM-related errors"""
    pass


class LLMConnectionError(LLMError):
    """Cannot connect to LLM service"""

    def __init__(self, service: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Cannot connect to {service}",
            severity=ErrorSeverity.ERROR,
            user_message=f"{service} is not running. Make sure it's started.",
            error_code="LLM_CONNECTION_FAILED",
            details=details or {"service": service},
        )


class LLMResponseError(LLMError):
    """Error in LLM response"""

    def __init__(self, details: Optional[dict] = None):
        super().__init__(
            message="LLM generated invalid response",
            severity=ErrorSeverity.ERROR,
            user_message="Failed to get an answer. The LLM service may be overloaded.",
            error_code="LLM_RESPONSE_INVALID",
            details=details or {},
        )


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded"""

    def __init__(self, retry_after_ms: Optional[int] = None):
        super().__init__(
            message="LLM rate limit exceeded",
            severity=ErrorSeverity.WARNING,
            user_message="Too many requests. Please wait before asking again.",
            error_code="LLM_RATE_LIMITED",
            details={"retry_after_ms": retry_after_ms},
        )


# Configuration Errors
class ConfigError(InterviewAssistantError):
    """Configuration-related error"""

    def __init__(self, message: str, field: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Configuration error: {message}",
            severity=ErrorSeverity.ERROR,
            user_message=f"Invalid configuration for '{field}'. Check settings.",
            error_code="CONFIG_ERROR",
            details=details or {"field": field},
        )


# Validation Errors
class ValidationError(InterviewAssistantError):
    """Input validation failed"""

    def __init__(self, field: str, reason: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            severity=ErrorSeverity.ERROR,
            user_message=f"Invalid input for '{field}'. {reason}",
            error_code="VALIDATION_FAILED",
            details=details or {"field": field, "reason": reason},
        )


# Recovery Strategies
class RecoveryStrategy:
    """Base class for error recovery strategies"""

    @staticmethod
    def log_and_continue(error: InterviewAssistantError) -> bool:
        """Log error and continue execution"""
        error.log()
        return True

    @staticmethod
    def log_and_retry(error: InterviewAssistantError, max_retries: int = 3) -> bool:
        """Log error and retry operation"""
        error.log()
        return True

    @staticmethod
    def log_and_fallback(error: InterviewAssistantError, fallback_fn: Callable) -> Any:
        """Log error and use fallback function"""
        error.log()
        return fallback_fn()


# Decorators
def validate_input(
    validators: dict[str, Callable],
    on_error: str = "raise",  # "raise", "log", "return"
) -> Callable[[F], F]:
    """
    Decorator to validate function inputs

    Args:
        validators: Dict mapping parameter names to validation functions
        on_error: How to handle validation errors

    Example:
        @validate_input({
            "text": lambda x: len(x) > 0,
            "model": lambda x: x in ["tiny", "base", "small"],
        })
        def transcribe(text: str, model: str):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for param, validator in validators.items():
                value = kwargs.get(param)
                try:
                    if not validator(value):
                        raise ValueError(f"Validation failed for {param}")
                except Exception as e:
                    error = ValidationError(param, str(e))
                    if on_error == "raise":
                        error.log()
                        raise error
                    elif on_error == "log":
                        error.log()
                        return None
                    elif on_error == "return":
                        return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def handle_errors(
    error_types: Union[Type[Exception], tuple[Type[Exception], ...]] = InterviewAssistantError,
    default_return: Any = None,
    log_traceback: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to handle errors gracefully

    Args:
        error_types: Exception type(s) to catch
        default_return: Value to return on error
        log_traceback: Whether to log full traceback

    Example:
        @handle_errors(
            error_types=(AudioError, TranscriptionError),
            default_return="",
            log_traceback=True
        )
        def transcribe_audio():
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if isinstance(e, InterviewAssistantError):
                    e.log()
                else:
                    logger.error(
                        f"Unhandled error in {func.__name__}",
                        error_type=type(e).__name__,
                        error_message=str(e),
                    )
                    if log_traceback:
                        logger.error(
                            "Full traceback",
                            traceback=traceback.format_exc(),
                        )
                return default_return

        return wrapper

    return decorator


def with_retry(
    max_attempts: int = 3,
    backoff_ms: int = 100,
    error_types: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
) -> Callable[[F], F]:
    """
    Decorator to retry function on failure

    Args:
        max_attempts: Maximum number of attempts
        backoff_ms: Milliseconds to wait between retries
        error_types: Exception types to retry on

    Example:
        @with_retry(max_attempts=3, backoff_ms=500)
        def call_llm():
            ...
    """
    import time

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except error_types as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait_ms = backoff_ms * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed, retrying...",
                            wait_ms=wait_ms,
                            error=str(e),
                        )
                        time.sleep(wait_ms / 1000)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed",
                            error=str(last_error),
                        )

            raise last_error

        return wrapper

    return decorator
