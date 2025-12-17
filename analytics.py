#!/usr/bin/env python3
"""
Performance Analytics for MRO Supply Scraper
Tracks and analyzes scraping performance metrics
"""

import time
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceAnalytics:
    """
    Track and analyze scraper performance

    Metrics tracked:
    - Request times (p50, p90, p95, p99)
    - Success rate over time
    - Speed (products/second) timeline
    - Memory usage trend
    - Error distribution
    - Proxy IP rotation
    """

    def __init__(self, config=None):
        """
        Initialize performance analytics

        Args:
            config: Configuration object
        """
        self.config = config
        self.start_time = time.time()

        # Request timing (keep last 1000)
        self.request_times = deque(maxlen=1000)

        # Success/failure tracking
        self.success_count = 0
        self.failed_count = 0

        # Error distribution
        self.error_counts = defaultdict(int)

        # Proxy tracking
        self.proxy_ips_seen = set()
        self.requests_by_ip = defaultdict(int)

        # Timeline data (for charts)
        self.timeline_data = []
        self.last_timeline_update = time.time()

        # Performance snapshots (every 5 minutes)
        self.performance_snapshots = deque(maxlen=288)  # 24 hours worth

        # Speed tracking
        self.completed_products = 0
        self.speed_history = deque(maxlen=60)  # Last 60 measurements

        logger.info("Performance analytics initialized")

    def record_request(
        self,
        duration: float,
        success: bool,
        error_type: Optional[str] = None,
        proxy_ip: Optional[str] = None
    ):
        """
        Record a request for analytics

        Args:
            duration: Request duration in seconds
            success: Whether request succeeded
            error_type: Type of error if failed
            proxy_ip: Proxy IP used
        """
        # Record timing
        self.request_times.append(duration)

        # Record success/failure
        if success:
            self.success_count += 1
            self.completed_products += 1
        else:
            self.failed_count += 1
            if error_type:
                self.error_counts[error_type] += 1

        # Record proxy IP
        if proxy_ip:
            self.proxy_ips_seen.add(proxy_ip)
            self.requests_by_ip[proxy_ip] += 1

        # Update timeline if needed (every 60 seconds)
        if time.time() - self.last_timeline_update >= 60:
            self._update_timeline()

    def _update_timeline(self):
        """Update timeline data point"""
        current_time = time.time()
        elapsed_hours = (current_time - self.start_time) / 3600

        total = self.success_count + self.failed_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        # Calculate current speed
        speed = self._calculate_current_speed()

        datapoint = {
            'timestamp': current_time,
            'elapsed_hours': round(elapsed_hours, 2),
            'completed': self.completed_products,
            'success_rate': round(success_rate, 2),
            'speed': round(speed, 2),
            'unique_ips': len(self.proxy_ips_seen)
        }

        self.timeline_data.append(datapoint)
        self.last_timeline_update = current_time

        # Keep last 24 hours only
        cutoff_time = current_time - (24 * 3600)
        self.timeline_data = [
            d for d in self.timeline_data
            if d['timestamp'] > cutoff_time
        ]

    def _calculate_current_speed(self) -> float:
        """Calculate current products per second"""
        if not self.timeline_data or len(self.timeline_data) < 2:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                return self.completed_products / elapsed
            return 0.0

        # Use last two data points
        recent = self.timeline_data[-2:]
        time_diff = recent[1]['timestamp'] - recent[0]['timestamp']
        product_diff = recent[1]['completed'] - recent[0]['completed']

        if time_diff > 0:
            return product_diff / time_diff

        return 0.0

    def calculate_percentiles(self) -> Dict[str, float]:
        """
        Calculate request time percentiles

        Returns:
            dict: Percentile values (p50, p90, p95, p99)
        """
        if not self.request_times:
            return {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0}

        sorted_times = sorted(self.request_times)
        n = len(sorted_times)

        def percentile(p):
            k = (n - 1) * p
            f = int(k)
            c = f + 1 if f < n - 1 else f
            return sorted_times[f] + (k - f) * (sorted_times[c] - sorted_times[f])

        return {
            'p50': round(percentile(0.50), 3),
            'p90': round(percentile(0.90), 3),
            'p95': round(percentile(0.95), 3),
            'p99': round(percentile(0.99), 3)
        }

    def get_error_distribution(self, top_n: int = 10) -> List[Dict]:
        """
        Get error distribution

        Args:
            top_n: Number of top errors to return

        Returns:
            List of error dictionaries
        """
        sorted_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'error': error, 'count': count}
            for error, count in sorted_errors[:top_n]
        ]

    def get_proxy_stats(self) -> Dict:
        """
        Get proxy usage statistics

        Returns:
            dict: Proxy statistics
        """
        total_requests = sum(self.requests_by_ip.values())

        # Find most/least used IPs
        if self.requests_by_ip:
            most_used_ip = max(self.requests_by_ip.items(), key=lambda x: x[1])
            least_used_ip = min(self.requests_by_ip.items(), key=lambda x: x[1])
        else:
            most_used_ip = (None, 0)
            least_used_ip = (None, 0)

        return {
            'unique_ips': len(self.proxy_ips_seen),
            'total_requests': total_requests,
            'most_used_ip': most_used_ip[0],
            'most_used_count': most_used_ip[1],
            'least_used_ip': least_used_ip[0],
            'least_used_count': least_used_ip[1],
            'avg_requests_per_ip': (
                round(total_requests / len(self.proxy_ips_seen), 1)
                if self.proxy_ips_seen else 0
            )
        }

    def get_current_speed(self) -> float:
        """Get current products per second"""
        return self._calculate_current_speed()

    def get_average_speed(self) -> float:
        """Get overall average speed"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.completed_products / elapsed
        return 0.0

    def get_success_rate(self) -> float:
        """Get overall success rate"""
        total = self.success_count + self.failed_count
        if total > 0:
            return (self.success_count / total) * 100
        return 0.0

    def get_uptime_hours(self) -> float:
        """Get uptime in hours"""
        return (time.time() - self.start_time) / 3600

    def get_comprehensive_stats(self) -> Dict:
        """
        Get all statistics

        Returns:
            dict: Comprehensive statistics
        """
        total_requests = self.success_count + self.failed_count
        uptime_hours = self.get_uptime_hours()

        stats = {
            # Request statistics
            'total_requests': total_requests,
            'successful_requests': self.success_count,
            'failed_requests': self.failed_count,
            'success_rate': round(self.get_success_rate(), 2),

            # Timing
            'uptime_hours': round(uptime_hours, 2),
            'uptime_days': round(uptime_hours / 24, 2),

            # Speed
            'completed_products': self.completed_products,
            'current_speed': round(self.get_current_speed(), 3),
            'average_speed': round(self.get_average_speed(), 3),

            # Request times
            'percentiles': self.calculate_percentiles(),
            'avg_request_time': (
                round(sum(self.request_times) / len(self.request_times), 3)
                if self.request_times else 0
            ),

            # Errors
            'error_distribution': self.get_error_distribution(5),
            'unique_error_types': len(self.error_counts),

            # Proxies
            'proxy_stats': self.get_proxy_stats(),

            # Timestamps
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'current_time': datetime.now().isoformat()
        }

        return stats

    def get_timeline_data(self, hours: int = 24) -> List[Dict]:
        """
        Get timeline data for charts

        Args:
            hours: Number of hours to include

        Returns:
            List of timeline data points
        """
        cutoff_time = time.time() - (hours * 3600)

        return [
            d for d in self.timeline_data
            if d['timestamp'] > cutoff_time
        ]

    def detect_performance_degradation(self) -> Optional[Dict]:
        """
        Detect if performance has degraded significantly

        Returns:
            dict: Alert info if degradation detected, None otherwise
        """
        if len(self.timeline_data) < 12:  # Need at least 12 minutes of data
            return None

        # Compare recent performance (last 5 min) to baseline (5-10 min ago)
        recent_data = self.timeline_data[-5:]
        baseline_data = self.timeline_data[-10:-5]

        # Calculate averages
        recent_speed = sum(d['speed'] for d in recent_data) / len(recent_data)
        baseline_speed = sum(d['speed'] for d in baseline_data) / len(baseline_data)

        recent_success = sum(d['success_rate'] for d in recent_data) / len(recent_data)
        baseline_success = sum(d['success_rate'] for d in baseline_data) / len(baseline_data)

        # Check for significant drops
        speed_drop = ((baseline_speed - recent_speed) / baseline_speed * 100) if baseline_speed > 0 else 0
        success_drop = baseline_success - recent_success

        if speed_drop > 30 or success_drop > 10:
            return {
                'speed_drop_percent': round(speed_drop, 1),
                'success_drop_percent': round(success_drop, 1),
                'baseline_speed': round(baseline_speed, 3),
                'recent_speed': round(recent_speed, 3),
                'baseline_success': round(baseline_success, 1),
                'recent_success': round(recent_success, 1),
                'timestamp': datetime.now().isoformat()
            }

        return None

    def export_report(self, filepath: str):
        """
        Export performance report to JSON

        Args:
            filepath: Path to output file
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'statistics': self.get_comprehensive_stats(),
                'timeline': self.get_timeline_data(24)
            }

            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Performance report exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export report: {e}")

    def generate_daily_summary(self) -> Dict:
        """
        Generate daily summary for email

        Returns:
            dict: Summary statistics
        """
        stats = self.get_comprehensive_stats()

        # Estimate completion
        avg_speed = stats['average_speed']
        if avg_speed > 0 and hasattr(self.config, 'TOTAL_URLS'):
            remaining = self.config.TOTAL_URLS - self.completed_products
            eta_hours = remaining / (avg_speed * 3600)
        else:
            eta_hours = 0

        summary = {
            'completed': stats['completed_products'],
            'success_rate': stats['success_rate'],
            'avg_speed': stats['average_speed'],
            'uptime_hours': stats['uptime_hours'],
            'eta_hours': round(eta_hours, 1),
            'unique_ips': stats['proxy_stats']['unique_ips'],
            'top_errors': stats['error_distribution'][:3],
            'avg_request_time': stats['avg_request_time'],
            'p95_request_time': stats['percentiles']['p95']
        }

        return summary


if __name__ == '__main__':
    # Test analytics
    import random

    print("Performance Analytics Test")
    print("=" * 60)

    analytics = PerformanceAnalytics()

    # Simulate requests
    print("\n1. Simulating 100 requests...")
    for i in range(100):
        duration = random.uniform(0.5, 2.0)
        success = random.random() < 0.90
        error_type = None if success else random.choice(['timeout', 'rate_limit', 'parse_error'])
        proxy_ip = f"192.168.1.{random.randint(1, 20)}"

        analytics.record_request(duration, success, error_type, proxy_ip)

    # Get statistics
    print("\n2. Comprehensive Statistics:")
    stats = analytics.get_comprehensive_stats()

    # Print key metrics
    print(f"\n   Total Requests: {stats['total_requests']}")
    print(f"   Success Rate: {stats['success_rate']}%")
    print(f"   Average Speed: {stats['average_speed']:.3f} products/sec")
    print(f"   Uptime: {stats['uptime_hours']:.2f} hours")

    print(f"\n   Request Time Percentiles:")
    for p, value in stats['percentiles'].items():
        print(f"     {p}: {value}s")

    print(f"\n   Proxy Statistics:")
    proxy_stats = stats['proxy_stats']
    print(f"     Unique IPs: {proxy_stats['unique_ips']}")
    print(f"     Avg per IP: {proxy_stats['avg_requests_per_ip']}")

    print(f"\n   Top Errors:")
    for error in stats['error_distribution']:
        print(f"     {error['error']}: {error['count']}")

    # Export report
    print("\n3. Exporting report...")
    analytics.export_report("/tmp/analytics_test_report.json")
    print("   Report exported to /tmp/analytics_test_report.json")

    print("\n✅ Analytics test completed")
