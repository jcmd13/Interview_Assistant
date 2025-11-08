"""
Performance Metrics Collection Framework

Provides metrics collection for end-to-end latency tracking, component timing,
resource usage monitoring, and performance analysis.

Supports:
- Latency percentiles (p50, p95, p99)
- Per-component timing
- Resource monitoring (memory, CPU)
- Real-time metrics export
- Historical data retention
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque
from enum import Enum
import json
from datetime import datetime, timedelta

from src.core.logger import get_logger

logger = get_logger("system.metrics")


class MetricType(str, Enum):
    """Types of metrics to track"""
    LATENCY = "latency"  # End-to-end or component latency
    THROUGHPUT = "throughput"  # Operations per second
    ERROR_RATE = "error_rate"  # Percentage of failures
    MEMORY = "memory"  # Memory usage
    CPU = "cpu"  # CPU usage
    CUSTOM = "custom"  # User-defined metrics


class Component(str, Enum):
    """Application components"""
    AUDIO_CAPTURE = "audio.capture"
    AUDIO_PROCESSING = "audio.processing"
    TRANSCRIPTION = "transcription"
    LLM = "llm"
    WEBSOCKET = "websocket"
    SERVER = "server"
    CLIENT = "client"


@dataclass
class MetricPoint:
    """A single metric measurement"""
    timestamp: float
    component: str
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "component": self.component,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "metadata": self.metadata,
        }


@dataclass
class MetricStats:
    """Statistics for a set of metric points"""
    count: int
    min: float
    max: float
    mean: float
    median: float
    p50: float  # 50th percentile
    p95: float  # 95th percentile
    p99: float  # 99th percentile
    sum: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "count": self.count,
            "min": round(self.min, 2),
            "max": round(self.max, 2),
            "mean": round(self.mean, 2),
            "median": round(self.median, 2),
            "p50": round(self.p50, 2),
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2),
            "sum": round(self.sum, 2),
        }


class MetricsCollector:
    """
    Collects and analyzes performance metrics.

    Thread-safe metrics collection with configurable retention and analysis.
    """

    def __init__(
        self,
        max_points: int = 10000,
        retention_hours: int = 24,
    ):
        """
        Initialize metrics collector

        Args:
            max_points: Maximum number of metric points to retain
            retention_hours: Hours to retain historical data
        """
        self._lock = threading.RLock()
        self._metrics: Dict[str, deque] = {}
        self._max_points = max_points
        self._retention_hours = retention_hours
        self._start_time = time.time()

        logger.info(
            "Metrics collector initialized",
            max_points=max_points,
            retention_hours=retention_hours,
        )

    def record(
        self,
        component: str,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a metric point

        Args:
            component: Component name
            metric_type: Type of metric
            value: Metric value
            metadata: Optional metadata
        """
        with self._lock:
            key = f"{component}_{metric_type.value}"

            if key not in self._metrics:
                self._metrics[key] = deque(maxlen=self._max_points)

            point = MetricPoint(
                timestamp=time.time(),
                component=component,
                metric_type=metric_type,
                value=value,
                metadata=metadata or {},
            )

            self._metrics[key].append(point)

            # Log if threshold exceeded
            if metric_type == MetricType.LATENCY:
                if value > 4000:  # 4s threshold
                    logger.warning(
                        "Latency threshold exceeded",
                        component=component,
                        latency_ms=round(value, 2),
                        threshold_ms=4000,
                    )

    def get_stats(
        self,
        component: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        minutes: int = 60,
    ) -> Dict[str, Any]:
        """
        Get statistics for metrics

        Args:
            component: Optional component filter
            metric_type: Optional metric type filter
            minutes: How far back to analyze (0 = all)

        Returns:
            Dictionary of statistics by component/type
        """
        with self._lock:
            cutoff_time = time.time() - (minutes * 60) if minutes > 0 else 0
            stats = {}

            for key, points in self._metrics.items():
                key_component, key_type = key.rsplit("_", 1)

                # Apply filters
                if component and key_component != component:
                    continue
                if metric_type and key_type != metric_type.value:
                    continue

                # Filter by time
                filtered = [p for p in points if p.timestamp >= cutoff_time]
                if not filtered:
                    continue

                # Calculate statistics
                values = [p.value for p in filtered]
                values.sort()

                stats[key] = MetricStats(
                    count=len(values),
                    min=min(values),
                    max=max(values),
                    mean=sum(values) / len(values),
                    median=values[len(values) // 2],
                    p50=self._percentile(values, 50),
                    p95=self._percentile(values, 95),
                    p99=self._percentile(values, 99),
                    sum=sum(values),
                )

            return {k: v.to_dict() for k, v in stats.items()}

    def get_recent(
        self,
        component: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get recent metric points

        Args:
            component: Optional component filter
            metric_type: Optional metric type filter
            limit: Maximum points to return

        Returns:
            List of metric points
        """
        with self._lock:
            results = []

            for key, points in self._metrics.items():
                key_component, key_type = key.rsplit("_", 1)

                # Apply filters
                if component and key_component != component:
                    continue
                if metric_type and key_type != metric_type.value:
                    continue

                results.extend(points)

            # Sort by timestamp and limit
            results.sort(key=lambda p: p.timestamp, reverse=True)
            return [p.to_dict() for p in results[:limit]]

    def export_json(self) -> str:
        """Export all metrics as JSON"""
        with self._lock:
            data = {
                "collected_at": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self._start_time,
                "stats": self.get_stats(),
                "recent": self.get_recent(limit=1000),
            }
            return json.dumps(data, indent=2)

    def clear(
        self,
        component: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
    ) -> None:
        """
        Clear metrics

        Args:
            component: Optional component to clear
            metric_type: Optional metric type to clear
        """
        with self._lock:
            if not component and not metric_type:
                self._metrics.clear()
                logger.info("All metrics cleared")
                return

            keys_to_remove = []
            for key in self._metrics:
                key_component, key_type = key.rsplit("_", 1)
                if component and key_component != component:
                    continue
                if metric_type and key_type != metric_type.value:
                    continue
                keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._metrics[key]

            logger.info(
                "Metrics cleared",
                component=component,
                metric_type=metric_type,
                count=len(keys_to_remove),
            )

    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_uptime(self) -> float:
        """Get collector uptime in seconds"""
        return time.time() - self._start_time


class LatencyTracker:
    """Context manager for tracking latency"""

    def __init__(
        self,
        collector: MetricsCollector,
        component: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize latency tracker

        Args:
            collector: MetricsCollector instance
            component: Component name
            metadata: Optional metadata
        """
        self.collector = collector
        self.component = component
        self.metadata = metadata or {}
        self.start_time = None

    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record"""
        if self.start_time is None:
            return

        latency_ms = (time.time() - self.start_time) * 1000
        self.collector.record(
            component=self.component,
            metric_type=MetricType.LATENCY,
            value=latency_ms,
            metadata={
                **self.metadata,
                "error": exc_type is not None,
                "error_type": exc_type.__name__ if exc_type else None,
            },
        )

        if exc_type:
            logger.error(
                "Component execution failed",
                component=self.component,
                latency_ms=round(latency_ms, 2),
                error=str(exc_val),
            )


# Global metrics collector instance
_collector: Optional[MetricsCollector] = None
_collector_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _collector
    if _collector is None:
        with _collector_lock:
            if _collector is None:
                _collector = MetricsCollector()
    return _collector


def track_latency(
    component: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> LatencyTracker:
    """
    Create a latency tracker

    Usage:
        with track_latency("transcription", {"model": "base"}):
            result = transcriber.transcribe(audio)
    """
    return LatencyTracker(get_metrics_collector(), component, metadata)


def record_metric(
    component: str,
    metric_type: MetricType,
    value: float,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Record a metric

    Args:
        component: Component name
        metric_type: Type of metric
        value: Metric value
        metadata: Optional metadata
    """
    get_metrics_collector().record(component, metric_type, value, metadata)


def get_metrics_summary(minutes: int = 60) -> Dict[str, Any]:
    """
    Get metrics summary

    Args:
        minutes: Time window in minutes (0 = all)

    Returns:
        Summary statistics
    """
    collector = get_metrics_collector()
    return {
        "uptime_seconds": round(collector.get_uptime()),
        "stats": collector.get_stats(minutes=minutes),
    }
