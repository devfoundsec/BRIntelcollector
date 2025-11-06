"""Metrics collection and Prometheus integration."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

from .logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class MetricValue:
    """Container for a single metric value with timestamp."""

    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics for the application.

    Thread-safe metrics collection with support for counters, gauges, and histograms.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = Lock()

        # Counters (monotonically increasing)
        self._counters: Dict[str, float] = defaultdict(float)

        # Gauges (can go up and down)
        self._gauges: Dict[str, float] = defaultdict(float)

        # Histograms (track distributions)
        self._histograms: Dict[str, List[float]] = defaultdict(list)

        # Labeled metrics
        self._labeled_metrics: Dict[str, Dict[str, MetricValue]] = defaultdict(dict)

        # Timing metrics
        self._timings: Dict[str, List[float]] = defaultdict(list)

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.

        Args:
            name: Metric name.
            value: Value to increment by.
            labels: Optional labels for the metric.
        """
        with self._lock:
            if labels:
                label_key = self._serialize_labels(labels)
                if name not in self._labeled_metrics:
                    self._labeled_metrics[name] = {}
                if label_key in self._labeled_metrics[name]:
                    self._labeled_metrics[name][label_key].value += value
                else:
                    self._labeled_metrics[name][label_key] = MetricValue(value, labels=labels)
            else:
                self._counters[name] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric to a specific value.

        Args:
            name: Metric name.
            value: Value to set.
            labels: Optional labels for the metric.
        """
        with self._lock:
            if labels:
                label_key = self._serialize_labels(labels)
                if name not in self._labeled_metrics:
                    self._labeled_metrics[name] = {}
                self._labeled_metrics[name][label_key] = MetricValue(value, labels=labels)
            else:
                self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        """Record an observation for a histogram.

        Args:
            name: Metric name.
            value: Value to observe.
        """
        with self._lock:
            self._histograms[name].append(value)
            # Keep only last 1000 observations
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-1000:]

    def time_operation(self, name: str, duration: float) -> None:
        """Record the duration of an operation.

        Args:
            name: Operation name.
            duration: Duration in seconds.
        """
        with self._lock:
            self._timings[name].append(duration)
            # Keep only last 1000 timings
            if len(self._timings[name]) > 1000:
                self._timings[name] = self._timings[name][-1000:]

    def get_counter(self, name: str) -> float:
        """Get the current value of a counter.

        Args:
            name: Counter name.

        Returns:
            Current counter value.
        """
        with self._lock:
            return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> float:
        """Get the current value of a gauge.

        Args:
            name: Gauge name.

        Returns:
            Current gauge value.
        """
        with self._lock:
            return self._gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a histogram.

        Args:
            name: Histogram name.

        Returns:
            Dictionary with min, max, mean, median, p95, p99.
        """
        with self._lock:
            values = self._histograms.get(name, [])

            if not values:
                return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0, "p95": 0, "p99": 0}

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": sum(sorted_values) / count,
                "median": sorted_values[count // 2],
                "p95": sorted_values[int(count * 0.95)],
                "p99": sorted_values[int(count * 0.99)],
            }

    def get_timing_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for operation timings.

        Args:
            name: Operation name.

        Returns:
            Dictionary with timing statistics.
        """
        with self._lock:
            values = self._timings.get(name, [])

            if not values:
                return {"count": 0, "total": 0, "min": 0, "max": 0, "mean": 0}

            return {
                "count": len(values),
                "total": sum(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
            }

    def get_all_metrics(self) -> Dict[str, any]:
        """Get all collected metrics.

        Returns:
            Dictionary with all metrics.
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name) for name in self._histograms
                },
                "timings": {name: self.get_timing_stats(name) for name in self._timings},
                "labeled": self._serialize_labeled_metrics(),
            }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            Metrics in Prometheus exposition format.
        """
        lines = []

        with self._lock:
            # Export counters
            for name, value in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")

            # Export gauges
            for name, value in self._gauges.items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

            # Export histograms
            for name, values in self._histograms.items():
                if not values:
                    continue

                lines.append(f"# TYPE {name} histogram")
                sorted_values = sorted(values)
                count = len(sorted_values)
                total = sum(sorted_values)

                # Buckets
                buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                for bucket in buckets:
                    bucket_count = sum(1 for v in sorted_values if v <= bucket)
                    lines.append(f'{name}_bucket{{le="{bucket}"}} {bucket_count}')

                lines.append(f'{name}_bucket{{le="+Inf"}} {count}')
                lines.append(f"{name}_sum {total}")
                lines.append(f"{name}_count {count}")

            # Export labeled metrics
            for name, label_dict in self._labeled_metrics.items():
                for label_key, metric_value in label_dict.items():
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in metric_value.labels.items()
                    )
                    lines.append(f"{name}{{{label_str}}} {metric_value.value}")

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._labeled_metrics.clear()
            self._timings.clear()

    def _serialize_labels(self, labels: Dict[str, str]) -> str:
        """Serialize labels to a string key."""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def _serialize_labeled_metrics(self) -> Dict[str, List[Dict]]:
        """Serialize labeled metrics for JSON export."""
        result = {}
        for name, label_dict in self._labeled_metrics.items():
            result[name] = [
                {"labels": metric_value.labels, "value": metric_value.value}
                for metric_value in label_dict.values()
            ]
        return result


# Global metrics collector instance
GLOBAL_METRICS = MetricsCollector()


class Timer:
    """Context manager for timing operations."""

    def __init__(self, metric_name: str, collector: Optional[MetricsCollector] = None):
        """Initialize timer.

        Args:
            metric_name: Name of the metric to record.
            collector: Metrics collector to use. Defaults to global collector.
        """
        self.metric_name = metric_name
        self.collector = collector or GLOBAL_METRICS
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start the timer."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and record the duration."""
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.collector.time_operation(self.metric_name, duration)


def track_api_call(source: str, success: bool = True) -> None:
    """Track an API call to a specific source.

    Args:
        source: Source name.
        success: Whether the call was successful.
    """
    GLOBAL_METRICS.increment(
        "api_calls_total", 1.0, labels={"source": source, "status": "success" if success else "error"}
    )


def track_indicators_collected(source: str, count: int) -> None:
    """Track the number of indicators collected from a source.

    Args:
        source: Source name.
        count: Number of indicators collected.
    """
    GLOBAL_METRICS.increment("indicators_collected_total", float(count), labels={"source": source})


def track_error(error_type: str, source: Optional[str] = None) -> None:
    """Track an error occurrence.

    Args:
        error_type: Type of error.
        source: Optional source where the error occurred.
    """
    labels = {"error_type": error_type}
    if source:
        labels["source"] = source

    GLOBAL_METRICS.increment("errors_total", 1.0, labels=labels)
