"""
Telemetry and Performance Monitoring

This module provides latency tracking and performance monitoring for the Interview Assistant.
It tracks end-to-end latency through the pipeline and individual stage timings.

Key Features:
- LatencyTracker context manager for automatic timing
- Pipeline stage tracking (audio capture, transcription, question detection, LLM)
- End-to-end latency calculation
- Integration with structured logging
- Latency budget warnings

Performance Target: <4s end-to-end latency (p95)
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime

from src.logging_config import get_logger


# ============================================================================
# Configuration
# ============================================================================

# Latency budgets (milliseconds) - warn if exceeded
LATENCY_BUDGETS = {
    "audio_capture": 500,
    "audio_preprocessing": 200,
    "transcription": 1000,
    "question_detection": 100,
    "llm_generation": 3000,
    "total_end_to_end": 4000,
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class LatencyMetrics:
    """
    Container for latency measurements across the pipeline.

    All durations are in milliseconds.
    """
    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Pipeline stage durations (ms)
    audio_capture_ms: Optional[float] = None
    audio_preprocessing_ms: Optional[float] = None
    transcription_ms: Optional[float] = None
    question_detection_ms: Optional[float] = None
    llm_generation_ms: Optional[float] = None
    term_explanation_ms: Optional[float] = None

    # Total end-to-end
    total_end_to_end_ms: Optional[float] = None

    # Metadata
    component: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)

    def get_total(self) -> float:
        """Calculate total latency from all stages."""
        total = 0.0
        for field_name, value in asdict(self).items():
            if field_name.endswith("_ms") and value is not None:
                total += value
        return total

    def check_budgets(self) -> List[str]:
        """
        Check if any stage exceeded its latency budget.

        Returns:
            List of warning messages for budget violations
        """
        warnings = []

        # Check individual stages
        stage_mapping = {
            "audio_capture_ms": "audio_capture",
            "audio_preprocessing_ms": "audio_preprocessing",
            "transcription_ms": "transcription",
            "question_detection_ms": "question_detection",
            "llm_generation_ms": "llm_generation",
        }

        for field_name, budget_key in stage_mapping.items():
            value = getattr(self, field_name, None)
            budget = LATENCY_BUDGETS.get(budget_key)

            if value is not None and budget is not None and value > budget:
                warnings.append(
                    f"{budget_key}: {value:.1f}ms (budget: {budget}ms, "
                    f"over by {value - budget:.1f}ms)"
                )

        # Check total end-to-end
        if self.total_end_to_end_ms is not None:
            budget = LATENCY_BUDGETS["total_end_to_end"]
            if self.total_end_to_end_ms > budget:
                warnings.append(
                    f"total_end_to_end: {self.total_end_to_end_ms:.1f}ms "
                    f"(budget: {budget}ms, over by {self.total_end_to_end_ms - budget:.1f}ms)"
                )

        return warnings


# ============================================================================
# Latency Tracker
# ============================================================================

class LatencyTracker:
    """
    Context manager for tracking operation latency.

    Usage:
        >>> tracker = LatencyTracker(request_id="req_123")
        >>> with tracker.track("transcription"):
        ...     result = transcribe_audio(audio_data)
        >>> tracker.metrics.transcription_ms  # Contains elapsed time
        >>> logger.info("latency_report", **tracker.metrics.to_dict())

    Or use the helper context manager:
        >>> with track_latency("req_123", "llm_generation") as tracker:
        ...     answer = generate_answer(question)
        >>> print(tracker.metrics.llm_generation_ms)
    """

    def __init__(self, request_id: str, component: Optional[str] = None):
        """
        Initialize latency tracker.

        Args:
            request_id: Request ID for correlation
            component: Component name for logging context
        """
        self.request_id = request_id
        self.component = component or "telemetry"
        self.metrics = LatencyMetrics(request_id=request_id, component=component)
        self.logger = get_logger(f"telemetry.{self.component}", request_id=request_id)

        # Track pipeline start time for end-to-end calculation
        self._pipeline_start: Optional[float] = None
        self._stage_start: Optional[float] = None
        self._current_stage: Optional[str] = None

    def start_pipeline(self) -> None:
        """Mark the start of an end-to-end pipeline operation."""
        self._pipeline_start = time.perf_counter()
        self.logger.debug("pipeline_started", request_id=self.request_id)

    def end_pipeline(self) -> float:
        """
        Mark the end of the pipeline and calculate total latency.

        Returns:
            Total end-to-end latency in milliseconds
        """
        if self._pipeline_start is None:
            self.logger.warning("end_pipeline_called_without_start")
            return 0.0

        elapsed = (time.perf_counter() - self._pipeline_start) * 1000
        self.metrics.total_end_to_end_ms = elapsed

        # Check budget violations
        warnings = self.metrics.check_budgets()
        if warnings:
            self.logger.warning(
                "latency_budget_exceeded",
                violations=warnings,
                total_ms=elapsed
            )
        else:
            self.logger.info(
                "pipeline_completed",
                total_ms=elapsed,
                within_budget=True
            )

        return elapsed

    @contextmanager
    def track(self, stage: str):
        """
        Context manager to track a specific pipeline stage.

        Args:
            stage: Stage name (e.g., "transcription", "llm_generation")

        Example:
            >>> with tracker.track("question_detection"):
            ...     questions = detect_questions(text)
        """
        self._current_stage = stage
        self._stage_start = time.perf_counter()

        try:
            yield self
        except Exception as e:
            self.metrics.success = False
            self.metrics.error = str(e)
            self.logger.error(
                f"{stage}_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        finally:
            if self._stage_start is not None:
                elapsed = (time.perf_counter() - self._stage_start) * 1000

                # Store in the appropriate metric field
                field_name = f"{stage}_ms"
                if hasattr(self.metrics, field_name):
                    setattr(self.metrics, field_name, elapsed)

                # Log the stage completion
                budget = LATENCY_BUDGETS.get(stage)
                over_budget = budget is not None and elapsed > budget

                self.logger.info(
                    f"{stage}_completed",
                    duration_ms=round(elapsed, 2),
                    budget_ms=budget,
                    over_budget=over_budget
                )

                self._stage_start = None
                self._current_stage = None

    def log_metrics(self) -> None:
        """Log the current metrics as a structured event."""
        self.logger.info("latency_metrics", **self.metrics.to_dict())


# ============================================================================
# Convenience Functions
# ============================================================================

@contextmanager
def track_latency(
    request_id: str,
    stage: str,
    component: Optional[str] = None
):
    """
    Simple context manager for tracking a single operation.

    Args:
        request_id: Request ID for correlation
        stage: Stage name (e.g., "transcription")
        component: Optional component name

    Yields:
        LatencyTracker instance

    Example:
        >>> with track_latency("req_abc", "llm_generation", "llm.analyzer") as tracker:
        ...     answer = generate_answer(question)
        >>> print(f"LLM took {tracker.metrics.llm_generation_ms}ms")
    """
    tracker = LatencyTracker(request_id=request_id, component=component)
    with tracker.track(stage):
        yield tracker


def track_function_latency(stage: str, component: Optional[str] = None):
    """
    Decorator to automatically track function execution time.

    Args:
        stage: Stage name for the latency metric
        component: Optional component name

    Example:
        >>> @track_function_latency("transcription", "whisper")
        >>> async def transcribe_audio(audio_bytes):
        ...     # ... transcription logic
        ...     return text
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            request_id = kwargs.get("request_id", "unknown")
            with track_latency(request_id, stage, component) as tracker:
                result = await func(*args, **kwargs)
                tracker.log_metrics()
                return result

        def sync_wrapper(*args, **kwargs):
            request_id = kwargs.get("request_id", "unknown")
            with track_latency(request_id, stage, component) as tracker:
                result = func(*args, **kwargs)
                tracker.log_metrics()
                return result

        # Return the appropriate wrapper based on whether the function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# Statistics Aggregation (for future performance monitoring)
# ============================================================================

class LatencyAggregator:
    """
    Aggregates latency metrics for percentile calculation.

    This will be used in Phase 4 for advanced performance monitoring.
    """

    def __init__(self):
        self.samples: Dict[str, List[float]] = {}
        self.logger = get_logger("telemetry.aggregator")

    def record(self, metrics: LatencyMetrics) -> None:
        """Record a latency measurement."""
        for field_name, value in asdict(metrics).items():
            if field_name.endswith("_ms") and value is not None:
                if field_name not in self.samples:
                    self.samples[field_name] = []
                self.samples[field_name].append(value)

    def get_percentiles(self, stage: str, percentiles: List[int] = [50, 95, 99]) -> Dict[int, float]:
        """
        Calculate percentiles for a specific stage.

        Args:
            stage: Stage name (e.g., "transcription_ms")
            percentiles: List of percentiles to calculate (e.g., [50, 95, 99])

        Returns:
            Dictionary mapping percentile to value

        Example:
            >>> agg = LatencyAggregator()
            >>> # ... record many samples
            >>> p95 = agg.get_percentiles("total_end_to_end_ms", [95])[95]
        """
        if stage not in self.samples or not self.samples[stage]:
            return {p: 0.0 for p in percentiles}

        import statistics
        sorted_samples = sorted(self.samples[stage])
        n = len(sorted_samples)

        result = {}
        for p in percentiles:
            index = int(n * p / 100)
            result[p] = sorted_samples[min(index, n - 1)]

        return result

    def clear(self) -> None:
        """Clear all recorded samples."""
        self.samples.clear()
        self.logger.info("samples_cleared")
