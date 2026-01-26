# =============================================================================
# Agent Twitter - Monitoring & Metrics
# =============================================================================
#
# Provides monitoring, metrics, and health check functionality.
#
# Features:
# - Health checks for all services
# - Metrics collection (requests, errors, latency)
# - Performance monitoring
# - Resource usage tracking
#
# =============================================================================

import time
import psutil
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps


# =============================================================================
# Metrics Storage
# =============================================================================


@dataclass
class MetricPoint:
    """A single metric data point"""

    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""

    count: int
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float


class MetricsRegistry:
    """Registry for storing and querying metrics"""

    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric value"""
        metric = MetricPoint(timestamp=time.time(), value=value, tags=tags or {})
        self._metrics[name].append(metric)

        # Prune old metrics if over limit
        if len(self._metrics[name]) > self.max_points:
            self._metrics[name] = self._metrics[name][-self.max_points :]

    def increment_counter(
        self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter"""
        key = self._make_key(name, tags)
        self._counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def get_metric(self, name: str, since: Optional[float] = None) -> List[MetricPoint]:
        """Get metric points"""
        if since:
            return [m for m in self._metrics[name] if m.timestamp >= since]
        return self._metrics[name].copy()

    def get_metric_summary(
        self, name: str, since: Optional[float] = None
    ) -> Optional[MetricSummary]:
        """Get summary statistics for a metric"""
        points = self.get_metric(name, since)
        if not points:
            return None

        values = [p.value for p in points]
        values.sort()

        import statistics

        return MetricSummary(
            count=len(values),
            min=min(values),
            max=max(values),
            avg=statistics.mean(values),
            p50=values[len(values) // 2],
            p95=values[int(len(values) * 0.95)] if len(values) > 1 else values[0],
            p99=values[int(len(values) * 0.99)] if len(values) > 1 else values[0],
        )

    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        return self._counters[self._make_key(name, tags)]

    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        return self._gauges[self._make_key(name, tags)]

    def reset_counters(self):
        """Reset all counters"""
        self._counters.clear()

    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Make a key for counters/gauges with tags"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}@{tag_str}"


# =============================================================================
# Request Tracking
# =============================================================================


class RequestTracker:
    """Track HTTP requests for monitoring"""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry

    def track_request(
        self, endpoint: str, method: str, status_code: int, duration: float
    ):
        """Track a request"""
        # Record request count
        self.registry.increment_counter(
            "http_requests_total",
            tags={"endpoint": endpoint, "method": method, "status": str(status_code)},
        )

        # Record duration
        self.registry.record_metric(
            "http_request_duration_ms",
            duration * 1000,
            tags={"endpoint": endpoint, "method": method},
        )

        # Track errors
        if status_code >= 400:
            self.registry.increment_counter(
                "http_errors_total",
                tags={
                    "endpoint": endpoint,
                    "method": method,
                    "status": str(status_code),
                },
            )


# =============================================================================
# Health Checks
# =============================================================================


class HealthCheck:
    """Base class for health checks"""

    def __init__(self, name: str):
        self.name = name

    def check(self) -> Dict[str, any]:
        """Perform the health check"""
        raise NotImplementedError


class ServiceHealthCheck(HealthCheck):
    """Health check for external services"""

    def __init__(self, name: str, check_func: callable, timeout: float = 5.0):
        super().__init__(name)
        self.check_func = check_func
        self.timeout = timeout

    def check(self) -> Dict[str, any]:
        """Check if service is healthy"""
        start = time.time()
        try:
            result = self.check_func()
            duration = time.time() - start
            return {
                "name": self.name,
                "status": "healthy" if result else "unhealthy",
                "latency_ms": round(duration * 1000, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            duration = time.time() - start
            return {
                "name": self.name,
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": round(duration * 1000, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }


class SystemHealthCheck(HealthCheck):
    """Health check for system resources"""

    def __init__(self, name: str, threshold_percent: float = 90.0):
        super().__init__(name)
        self.threshold_percent = threshold_percent

    def check(self) -> Dict[str, any]:
        """Check system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        cpu_healthy = cpu_percent < self.threshold_percent
        memory_healthy = memory.percent < self.threshold_percent
        disk_healthy = disk.percent < self.threshold_percent

        return {
            "name": self.name,
            "status": "healthy"
            if all([cpu_healthy, memory_healthy, disk_healthy])
            else "degraded",
            "cpu": {"percent": cpu_percent, "healthy": cpu_healthy},
            "memory": {
                "percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "healthy": memory_healthy,
            },
            "disk": {
                "percent": disk.percent,
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "healthy": disk_healthy,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# =============================================================================
# Health Monitor
# =============================================================================


class HealthMonitor:
    """Monitors health of all services and system resources"""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.checks: List[HealthCheck] = []
        self.last_results: Dict[str, Dict] = {}

    def add_check(self, check: HealthCheck):
        """Add a health check"""
        self.checks.append(check)

    def run_checks(self) -> Dict[str, any]:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"

        for check in self.checks:
            result = check.check()
            self.last_results[check.name] = result
            results[check.name] = result

            if result["status"] == "unhealthy":
                overall_status = "unhealthy"
            elif result["status"] == "degraded" and overall_status != "unhealthy":
                overall_status = "degraded"

        # Record health status
        self.registry.set_gauge(
            "health_status", 1 if overall_status == "healthy" else 0
        )

        return {
            "status": overall_status,
            "checks": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_status(self) -> Dict[str, any]:
        """Get last known health status"""
        return {
            "status": self._compute_overall_status(),
            "checks": self.last_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _compute_overall_status(self) -> str:
        """Compute overall health status from last results"""
        if not self.last_results:
            return "unknown"

        statuses = [r.get("status", "unknown") for r in self.last_results.values()]

        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"


# =============================================================================
# Monitoring Decorator
# =============================================================================


def track_endpoint(monitor: "MonitoringService"):
    """Decorator to track endpoint calls"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            status_code = 200
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                error = str(e)
                raise
            finally:
                duration = time.time() - start
                # Get endpoint name from function
                endpoint = getattr(func, "__name__", "unknown")
                monitor.tracker.track_request(endpoint, "POST", status_code, duration)

        return wrapper

    return decorator


# =============================================================================
# Monitoring Service
# =============================================================================


class MonitoringService:
    """Main monitoring service"""

    def __init__(self):
        self.registry = MetricsRegistry()
        self.tracker = RequestTracker(self.registry)
        self.health = HealthMonitor(self.registry)

        # Add default health checks
        self.health.add_check(SystemHealthCheck("system"))

    def get_metrics(self, since: Optional[timedelta] = None) -> Dict[str, any]:
        """Get all metrics"""
        since_ts = time.time() - since.total_seconds() if since else None

        metrics = {}

        # Get counter values
        metrics["counters"] = {}
        for key in self.registry._counters:
            metrics["counters"][key] = self.registry.get_counter(
                key.split("@")[0], self._parse_tags(key)
            )

        # Get gauge values
        metrics["gauges"] = {}
        for key in self.registry._gauges:
            metrics["gauges"][key] = self.registry.get_gauge(
                key.split("@")[0], self._parse_tags(key)
            )

        # Get metric summaries
        metrics["summaries"] = {}
        for name in self.registry._metrics:
            summary = self.registry.get_metric_summary(name, since_ts)
            if summary:
                metrics["summaries"][name] = {
                    "count": summary.count,
                    "min": round(summary.min, 3),
                    "max": round(summary.max, 3),
                    "avg": round(summary.avg, 3),
                    "p50": round(summary.p50, 3),
                    "p95": round(summary.p95, 3),
                    "p99": round(summary.p99, 3),
                }

        return metrics

    def get_health(self) -> Dict[str, any]:
        """Get health status"""
        return self.health.run_checks()

    def _parse_tags(self, key: str) -> Optional[Dict[str, str]]:
        """Parse tags from a key"""
        if "@" not in key:
            return None
        tags_str = key.split("@")[1]
        tags = {}
        for tag in tags_str.split(","):
            if "=" in tag:
                k, v = tag.split("=")
                tags[k] = v
        return tags


# =============================================================================
# Global Instance
# =============================================================================

monitoring = MonitoringService()
