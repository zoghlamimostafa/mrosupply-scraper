#!/usr/bin/env python3
"""
Health Check System for MRO Supply Scraper
Monitors 8 different aspects of system health
"""

import time
import shutil
import logging
import requests
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class CheckResult:
    """Result of a single health check"""

    def __init__(self, healthy: bool, message: str, severity: str = "info", details: Optional[Dict] = None):
        self.healthy = healthy
        self.message = message
        self.severity = severity  # info, warning, critical
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'healthy': self.healthy,
            'message': self.message,
            'severity': self.severity,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        status = "✓" if self.healthy else "✗"
        return f"{status} [{self.severity.upper()}] {self.message}"


class HealthStatus:
    """Overall health status from all checks"""

    def __init__(self):
        self.progress_check: Optional[CheckResult] = None
        self.memory_check: Optional[CheckResult] = None
        self.disk_check: Optional[CheckResult] = None
        self.network_check: Optional[CheckResult] = None
        self.rate_limit_check: Optional[CheckResult] = None
        self.proxy_check: Optional[CheckResult] = None
        self.quality_check: Optional[CheckResult] = None
        self.success_rate_check: Optional[CheckResult] = None
        self.timestamp = datetime.now()

    @property
    def is_healthy(self) -> bool:
        """Check if all critical checks are healthy"""
        checks = [
            self.progress_check,
            self.memory_check,
            self.disk_check,
            self.network_check
        ]
        return all(c and c.healthy for c in checks if c)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings exist"""
        checks = [
            self.progress_check, self.memory_check, self.disk_check,
            self.network_check, self.rate_limit_check, self.proxy_check,
            self.quality_check, self.success_rate_check
        ]
        return any(c and c.severity == "warning" for c in checks if c)

    @property
    def has_criticals(self) -> bool:
        """Check if any critical issues exist"""
        checks = [
            self.progress_check, self.memory_check, self.disk_check,
            self.network_check, self.rate_limit_check, self.proxy_check,
            self.quality_check, self.success_rate_check
        ]
        return any(c and c.severity == "critical" for c in checks if c)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'is_healthy': self.is_healthy,
            'has_warnings': self.has_warnings,
            'has_criticals': self.has_criticals,
            'checks': {
                'progress': self.progress_check.to_dict() if self.progress_check else None,
                'memory': self.memory_check.to_dict() if self.memory_check else None,
                'disk': self.disk_check.to_dict() if self.disk_check else None,
                'network': self.network_check.to_dict() if self.network_check else None,
                'rate_limit': self.rate_limit_check.to_dict() if self.rate_limit_check else None,
                'proxy': self.proxy_check.to_dict() if self.proxy_check else None,
                'quality': self.quality_check.to_dict() if self.quality_check else None,
                'success_rate': self.success_rate_check.to_dict() if self.success_rate_check else None,
            },
            'timestamp': self.timestamp.isoformat()
        }


class HealthCheck:
    """Comprehensive health monitoring system"""

    def __init__(self, config, scraper=None):
        """Initialize health check system"""
        self.config = config
        self.scraper = scraper
        self.last_check_time = time.time()
        self.memory_history = deque(maxlen=60)  # Last 60 measurements
        self.check_history = []

    def perform_health_check(self) -> HealthStatus:
        """Perform all health checks"""
        status = HealthStatus()

        try:
            # 1. Progress check - is scraper making progress?
            status.progress_check = self.check_progress()

            # 2. Memory usage check
            status.memory_check = self.check_memory()

            # 3. Disk space check
            status.disk_check = self.check_disk_space()

            # 4. Network connectivity check
            status.network_check = self.check_network()

            # 5. Rate limit check
            status.rate_limit_check = self.check_rate_limits()

            # 6. Proxy health check
            status.proxy_check = self.check_proxy_health()

            # 7. Data quality check
            status.quality_check = self.check_data_quality()

            # 8. Success rate check
            status.success_rate_check = self.check_success_rate()

        except Exception as e:
            logger.error(f"Health check error: {e}")

        # Save health status
        self.save_health_status(status)
        self.check_history.append(status)

        # Keep only last 100 checks
        if len(self.check_history) > 100:
            self.check_history = self.check_history[-100:]

        self.last_check_time = time.time()

        return status

    def check_progress(self) -> CheckResult:
        """Check if checkpoint is being updated (scraper is making progress)"""
        checkpoint_file = self.config.OUTPUT_DIR / "checkpoint_products.json"

        if not checkpoint_file.exists():
            return CheckResult(
                healthy=True,  # OK if just starting
                message="No checkpoint file yet (starting up)",
                severity="info"
            )

        # Check file modification time
        try:
            mtime = checkpoint_file.stat().st_mtime
            age_minutes = (time.time() - mtime) / 60

            threshold = self.config.STALE_CHECKPOINT_MINUTES

            if age_minutes > threshold:
                return CheckResult(
                    healthy=False,
                    message=f"No progress for {age_minutes:.1f} minutes",
                    severity="critical",
                    details={"age_minutes": age_minutes, "threshold": threshold}
                )

            return CheckResult(
                healthy=True,
                message=f"Progress normal (updated {age_minutes:.1f} min ago)",
                severity="info",
                details={"age_minutes": age_minutes}
            )

        except Exception as e:
            return CheckResult(
                healthy=False,
                message=f"Error checking progress: {e}",
                severity="warning"
            )

    def check_memory(self) -> CheckResult:
        """Check memory usage and detect leaks"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_percent = process.memory_percent()

            # Record for leak detection
            self.memory_history.append({
                'mb': memory_mb,
                'time': time.time()
            })

            # Check threshold
            if memory_mb > self.config.MEMORY_THRESHOLD_MB:
                return CheckResult(
                    healthy=False,
                    message=f"High memory usage: {memory_mb:.0f}MB ({memory_percent:.1f}%)",
                    severity="critical",
                    details={"memory_mb": memory_mb, "memory_percent": memory_percent}
                )

            # Check for memory leak (growing over time)
            if len(self.memory_history) >= 10:
                memory_growth = self.calculate_memory_growth()
                if memory_growth > 100:  # 100MB/hour growth
                    return CheckResult(
                        healthy=False,
                        message=f"Possible memory leak: {memory_growth:.0f}MB/hour growth",
                        severity="warning",
                        details={"growth_rate_mb_per_hour": memory_growth, "current_mb": memory_mb}
                    )

            return CheckResult(
                healthy=True,
                message=f"Memory normal: {memory_mb:.0f}MB ({memory_percent:.1f}%)",
                severity="info",
                details={"memory_mb": memory_mb, "memory_percent": memory_percent}
            )

        except Exception as e:
            return CheckResult(
                healthy=False,
                message=f"Error checking memory: {e}",
                severity="warning"
            )

    def calculate_memory_growth(self) -> float:
        """Calculate memory growth rate in MB/hour"""
        if len(self.memory_history) < 2:
            return 0.0

        first = self.memory_history[0]
        last = self.memory_history[-1]

        time_diff_hours = (last['time'] - first['time']) / 3600
        if time_diff_hours < 0.1:  # Less than 6 minutes
            return 0.0

        mb_diff = last['mb'] - first['mb']
        return mb_diff / time_diff_hours

    def check_disk_space(self) -> CheckResult:
        """Check available disk space"""
        try:
            stats = shutil.disk_usage(str(self.config.OUTPUT_DIR))
            free_gb = stats.free / (1024**3)
            total_gb = stats.total / (1024**3)
            used_percent = (stats.used / stats.total) * 100

            threshold = self.config.DISK_SPACE_THRESHOLD_GB

            if free_gb < threshold:
                return CheckResult(
                    healthy=False,
                    message=f"Low disk space: {free_gb:.1f}GB free",
                    severity="critical",
                    details={"free_gb": free_gb, "total_gb": total_gb, "used_percent": used_percent}
                )

            # Warning threshold (2x the critical threshold)
            if free_gb < threshold * 2:
                return CheckResult(
                    healthy=True,  # Not critical yet
                    message=f"Disk space getting low: {free_gb:.1f}GB free",
                    severity="warning",
                    details={"free_gb": free_gb, "total_gb": total_gb, "used_percent": used_percent}
                )

            return CheckResult(
                healthy=True,
                message=f"Disk space OK: {free_gb:.1f}GB free ({100-used_percent:.1f}% available)",
                severity="info",
                details={"free_gb": free_gb, "used_percent": used_percent}
            )

        except Exception as e:
            return CheckResult(
                healthy=False,
                message=f"Error checking disk space: {e}",
                severity="warning"
            )

    def check_network(self) -> CheckResult:
        """Check network connectivity"""
        try:
            # Try to reach a reliable endpoint
            response = requests.get(
                "https://www.google.com",
                timeout=10
            )

            if response.status_code == 200:
                return CheckResult(
                    healthy=True,
                    message="Network connectivity OK",
                    severity="info"
                )
            else:
                return CheckResult(
                    healthy=False,
                    message=f"Network issue: HTTP {response.status_code}",
                    severity="warning",
                    details={"status_code": response.status_code}
                )

        except requests.exceptions.ConnectionError:
            return CheckResult(
                healthy=False,
                message="Network connection lost",
                severity="critical"
            )
        except requests.exceptions.Timeout:
            return CheckResult(
                healthy=False,
                message="Network timeout",
                severity="warning"
            )
        except Exception as e:
            return CheckResult(
                healthy=False,
                message=f"Network check failed: {str(e)}",
                severity="warning"
            )

    def check_rate_limits(self) -> CheckResult:
        """Check if we're being rate limited"""
        if not self.scraper:
            return CheckResult(healthy=True, message="No scraper instance", severity="info")

        try:
            rate_limit_count = getattr(self.scraper, 'rate_limit_count', 0)

            if rate_limit_count >= self.config.RATE_LIMIT_THRESHOLD:
                return CheckResult(
                    healthy=False,
                    message=f"Rate limited: {rate_limit_count} consecutive 429s",
                    severity="critical",
                    details={"count": rate_limit_count}
                )

            if rate_limit_count > 0:
                return CheckResult(
                    healthy=True,
                    message=f"Some rate limiting: {rate_limit_count} recent 429s",
                    severity="warning",
                    details={"count": rate_limit_count}
                )

            return CheckResult(
                healthy=True,
                message="No rate limiting issues",
                severity="info"
            )

        except Exception as e:
            return CheckResult(
                healthy=True,
                message=f"Could not check rate limits: {e}",
                severity="info"
            )

    def check_proxy_health(self) -> CheckResult:
        """Check proxy pool health"""
        if not self.scraper:
            return CheckResult(healthy=True, message="No scraper instance", severity="info")

        try:
            # Check if we're rotating through different IPs
            unique_ips = len(getattr(self.scraper, 'proxy_ips_seen', set()))

            if unique_ips == 0:
                return CheckResult(
                    healthy=True,
                    message="Proxy check: No requests yet",
                    severity="info"
                )

            if unique_ips < 10:
                return CheckResult(
                    healthy=True,
                    message=f"Limited proxy rotation: {unique_ips} unique IPs",
                    severity="warning",
                    details={"unique_ips": unique_ips}
                )

            return CheckResult(
                healthy=True,
                message=f"Proxy rotation OK: {unique_ips} unique IPs",
                severity="info",
                details={"unique_ips": unique_ips}
            )

        except Exception as e:
            return CheckResult(
                healthy=True,
                message=f"Could not check proxy health: {e}",
                severity="info"
            )

    def check_data_quality(self) -> CheckResult:
        """Check data quality metrics"""
        # This will be implemented when validator is integrated
        # For now, return OK
        return CheckResult(
            healthy=True,
            message="Data quality check not yet implemented",
            severity="info"
        )

    def check_success_rate(self) -> CheckResult:
        """Check overall success rate"""
        if not self.scraper:
            return CheckResult(healthy=True, message="No scraper instance", severity="info")

        try:
            success_count = getattr(self.scraper, 'success_count', 0)
            failed_count = getattr(self.scraper, 'failed_count', 0)
            total = success_count + failed_count

            if total == 0:
                return CheckResult(
                    healthy=True,
                    message="No products scraped yet",
                    severity="info"
                )

            success_rate = (success_count / total) * 100

            if success_rate < 50:
                return CheckResult(
                    healthy=False,
                    message=f"Very low success rate: {success_rate:.1f}%",
                    severity="critical",
                    details={"success_rate": success_rate, "success": success_count, "failed": failed_count}
                )

            if success_rate < 80:
                return CheckResult(
                    healthy=True,
                    message=f"Low success rate: {success_rate:.1f}%",
                    severity="warning",
                    details={"success_rate": success_rate, "success": success_count, "failed": failed_count}
                )

            return CheckResult(
                healthy=True,
                message=f"Success rate good: {success_rate:.1f}%",
                severity="info",
                details={"success_rate": success_rate, "success": success_count, "failed": failed_count}
            )

        except Exception as e:
            return CheckResult(
                healthy=True,
                message=f"Could not check success rate: {e}",
                severity="info"
            )

    def save_health_status(self, status: HealthStatus):
        """Save health status to file for dashboard"""
        try:
            status_file = self.config.OUTPUT_DIR / "health_status.json"
            with open(status_file, 'w') as f:
                json.dump(status.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health status: {e}")


if __name__ == '__main__':
    # Test health check system
    import sys
    sys.path.insert(0, '.')
    from config import Config

    try:
        config = Config()
        health_check = HealthCheck(config)

        print("Running health checks...\n")
        status = health_check.perform_health_check()

        print("Health Check Results:")
        print("=" * 60)

        checks = [
            ('Progress', status.progress_check),
            ('Memory', status.memory_check),
            ('Disk', status.disk_check),
            ('Network', status.network_check),
            ('Rate Limit', status.rate_limit_check),
            ('Proxy', status.proxy_check),
            ('Quality', status.quality_check),
            ('Success Rate', status.success_rate_check),
        ]

        for name, check in checks:
            if check:
                print(f"{name:15} {check}")

        print("=" * 60)
        print(f"Overall: {'✅ Healthy' if status.is_healthy else '❌ Unhealthy'}")

        if status.has_warnings:
            print("⚠️  Has warnings")
        if status.has_criticals:
            print("🚨 Has critical issues")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
