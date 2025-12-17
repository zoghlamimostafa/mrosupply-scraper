#!/usr/bin/env python3
"""
Cost Tracker for MRO Supply Scraper
Tracks bandwidth usage and estimates costs
"""

import time
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Track bandwidth and costs

    Estimates:
    - Proxy bandwidth usage
    - Proxy costs (based on data transfer)
    - Server costs (based on runtime)
    - Total cost per product
    """

    # Default cost rates (can be overridden in config)
    DEFAULT_PROXY_COST_PER_GB = 1.0      # $1 per GB
    DEFAULT_SERVER_COST_PER_HOUR = 0.10  # $0.10 per hour

    # Average sizes (bytes)
    AVG_REQUEST_SIZE = 1024              # 1 KB request
    AVG_RESPONSE_SIZE = 51200            # 50 KB response (HTML + images)

    def __init__(self, config=None):
        """
        Initialize cost tracker

        Args:
            config: Configuration object
        """
        self.config = config

        # Get cost rates from config or use defaults
        self.proxy_cost_per_gb = (
            getattr(config, 'PROXY_COST_PER_GB', self.DEFAULT_PROXY_COST_PER_GB)
            if config else self.DEFAULT_PROXY_COST_PER_GB
        )

        self.server_cost_per_hour = (
            getattr(config, 'SERVER_COST_PER_HOUR', self.DEFAULT_SERVER_COST_PER_HOUR)
            if config else self.DEFAULT_SERVER_COST_PER_HOUR
        )

        # Tracking
        self.start_time = time.time()
        self.total_requests = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

        # Products tracking
        self.successful_products = 0
        self.failed_products = 0

        logger.info(
            f"Cost tracker initialized: "
            f"proxy=${self.proxy_cost_per_gb}/GB, "
            f"server=${self.server_cost_per_hour}/hour"
        )

    def record_request(
        self,
        bytes_sent: Optional[int] = None,
        bytes_received: Optional[int] = None,
        success: bool = True
    ):
        """
        Record a request for cost tracking

        Args:
            bytes_sent: Bytes sent in request (uses average if None)
            bytes_received: Bytes received in response (uses average if None)
            success: Whether request was successful
        """
        self.total_requests += 1

        # Use averages if not provided
        if bytes_sent is None:
            bytes_sent = self.AVG_REQUEST_SIZE

        if bytes_received is None:
            bytes_received = self.AVG_RESPONSE_SIZE if success else 0

        self.total_bytes_sent += bytes_sent
        self.total_bytes_received += bytes_received

        if success:
            self.successful_products += 1
        else:
            self.failed_products += 1

    def get_bandwidth_usage_gb(self) -> float:
        """
        Get total bandwidth usage in GB

        Returns:
            float: Bandwidth in GB
        """
        total_bytes = self.total_bytes_sent + self.total_bytes_received
        return total_bytes / (1024 ** 3)

    def get_bandwidth_usage_mb(self) -> float:
        """
        Get total bandwidth usage in MB

        Returns:
            float: Bandwidth in MB
        """
        total_bytes = self.total_bytes_sent + self.total_bytes_received
        return total_bytes / (1024 ** 2)

    def get_uptime_hours(self) -> float:
        """
        Get uptime in hours

        Returns:
            float: Hours running
        """
        return (time.time() - self.start_time) / 3600

    def calculate_proxy_cost(self) -> float:
        """
        Calculate proxy cost based on bandwidth

        Returns:
            float: Estimated proxy cost in USD
        """
        bandwidth_gb = self.get_bandwidth_usage_gb()
        return bandwidth_gb * self.proxy_cost_per_gb

    def calculate_server_cost(self) -> float:
        """
        Calculate server cost based on runtime

        Returns:
            float: Estimated server cost in USD
        """
        uptime_hours = self.get_uptime_hours()
        return uptime_hours * self.server_cost_per_hour

    def calculate_total_cost(self) -> float:
        """
        Calculate total estimated cost

        Returns:
            float: Total cost in USD
        """
        return self.calculate_proxy_cost() + self.calculate_server_cost()

    def get_cost_per_product(self) -> float:
        """
        Calculate cost per successfully scraped product

        Returns:
            float: Cost per product in USD
        """
        if self.successful_products == 0:
            return 0.0

        return self.calculate_total_cost() / self.successful_products

    def get_statistics(self) -> Dict:
        """
        Get comprehensive cost statistics

        Returns:
            dict: Cost statistics
        """
        bandwidth_gb = self.get_bandwidth_usage_gb()
        bandwidth_mb = self.get_bandwidth_usage_mb()
        uptime_hours = self.get_uptime_hours()
        proxy_cost = self.calculate_proxy_cost()
        server_cost = self.calculate_server_cost()
        total_cost = self.calculate_total_cost()
        cost_per_product = self.get_cost_per_product()

        stats = {
            # Bandwidth
            'total_requests': self.total_requests,
            'total_bytes_sent': self.total_bytes_sent,
            'total_bytes_received': self.total_bytes_received,
            'total_bandwidth_mb': round(bandwidth_mb, 2),
            'total_bandwidth_gb': round(bandwidth_gb, 3),
            'avg_request_size_kb': round(
                self.total_bytes_sent / self.total_requests / 1024, 2
            ) if self.total_requests > 0 else 0,
            'avg_response_size_kb': round(
                self.total_bytes_received / self.total_requests / 1024, 2
            ) if self.total_requests > 0 else 0,

            # Runtime
            'uptime_hours': round(uptime_hours, 2),
            'uptime_days': round(uptime_hours / 24, 2),

            # Products
            'successful_products': self.successful_products,
            'failed_products': self.failed_products,
            'total_products': self.successful_products + self.failed_products,

            # Costs
            'proxy_cost_usd': round(proxy_cost, 2),
            'server_cost_usd': round(server_cost, 2),
            'total_cost_usd': round(total_cost, 2),
            'cost_per_product_usd': round(cost_per_product, 4),

            # Rates
            'proxy_cost_per_gb': self.proxy_cost_per_gb,
            'server_cost_per_hour': self.server_cost_per_hour,

            # Timestamps
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'current_time': datetime.now().isoformat()
        }

        return stats

    def estimate_total_cost(self, total_products: int) -> Dict:
        """
        Estimate total cost for scraping all products

        Args:
            total_products: Total number of products to scrape

        Returns:
            dict: Cost estimates
        """
        if self.successful_products == 0:
            return {
                'error': 'Insufficient data for estimation',
                'products_scraped': 0
            }

        # Calculate current rates
        current_speed = self.successful_products / self.get_uptime_hours()  # products/hour
        current_bandwidth_per_product = self.get_bandwidth_usage_gb() / self.successful_products

        # Estimate remaining
        remaining_products = total_products - self.successful_products
        remaining_hours = remaining_products / current_speed if current_speed > 0 else 0
        remaining_bandwidth_gb = remaining_products * current_bandwidth_per_product

        # Estimate costs
        remaining_proxy_cost = remaining_bandwidth_gb * self.proxy_cost_per_gb
        remaining_server_cost = remaining_hours * self.server_cost_per_hour
        remaining_total_cost = remaining_proxy_cost + remaining_server_cost

        # Total estimates
        total_bandwidth_gb = self.get_bandwidth_usage_gb() + remaining_bandwidth_gb
        total_hours = self.get_uptime_hours() + remaining_hours
        total_proxy_cost = self.calculate_proxy_cost() + remaining_proxy_cost
        total_server_cost = self.calculate_server_cost() + remaining_server_cost
        estimated_total_cost = self.calculate_total_cost() + remaining_total_cost

        estimate = {
            # Progress
            'products_scraped': self.successful_products,
            'products_remaining': remaining_products,
            'total_products': total_products,
            'completion_percent': round(
                (self.successful_products / total_products * 100), 2
            ),

            # Time estimates
            'hours_elapsed': round(self.get_uptime_hours(), 2),
            'hours_remaining': round(remaining_hours, 2),
            'total_hours': round(total_hours, 2),
            'days_remaining': round(remaining_hours / 24, 2),

            # Bandwidth estimates
            'bandwidth_used_gb': round(self.get_bandwidth_usage_gb(), 3),
            'bandwidth_remaining_gb': round(remaining_bandwidth_gb, 3),
            'total_bandwidth_gb': round(total_bandwidth_gb, 3),

            # Cost estimates
            'cost_so_far_usd': round(self.calculate_total_cost(), 2),
            'cost_remaining_usd': round(remaining_total_cost, 2),
            'estimated_total_cost_usd': round(estimated_total_cost, 2),

            # Breakdown
            'proxy_cost_so_far': round(self.calculate_proxy_cost(), 2),
            'proxy_cost_remaining': round(remaining_proxy_cost, 2),
            'proxy_cost_total': round(total_proxy_cost, 2),

            'server_cost_so_far': round(self.calculate_server_cost(), 2),
            'server_cost_remaining': round(remaining_server_cost, 2),
            'server_cost_total': round(total_server_cost, 2),

            # Efficiency
            'cost_per_product': round(estimated_total_cost / total_products, 4),
            'bandwidth_per_product_mb': round(
                total_bandwidth_gb * 1024 / total_products, 2
            ),
        }

        return estimate

    def export_report(self, filepath: str):
        """
        Export cost report to JSON

        Args:
            filepath: Path to output file
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }

            # Add estimate if we have enough data
            if self.successful_products > 100 and hasattr(self.config, 'TOTAL_URLS'):
                report['estimate'] = self.estimate_total_cost(self.config.TOTAL_URLS)

            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Cost report exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export cost report: {e}")

    def get_summary_text(self) -> str:
        """
        Get human-readable cost summary

        Returns:
            str: Cost summary text
        """
        stats = self.get_statistics()

        summary = f"""
Cost Summary:
  Bandwidth: {stats['total_bandwidth_gb']:.3f} GB
  Runtime: {stats['uptime_hours']:.1f} hours ({stats['uptime_days']:.1f} days)
  Products: {stats['successful_products']:,}

  Proxy Cost: ${stats['proxy_cost_usd']:.2f}
  Server Cost: ${stats['server_cost_usd']:.2f}
  Total Cost: ${stats['total_cost_usd']:.2f}

  Cost per Product: ${stats['cost_per_product_usd']:.4f}
        """.strip()

        return summary


if __name__ == '__main__':
    # Test cost tracker
    print("Cost Tracker Test")
    print("=" * 60)

    tracker = CostTracker()

    # Simulate requests
    print("\n1. Simulating 1000 successful requests...")
    for i in range(1000):
        tracker.record_request(success=True)

    # Simulate some failures
    print("2. Simulating 100 failed requests...")
    for i in range(100):
        tracker.record_request(bytes_received=0, success=False)

    # Get statistics
    print("\n3. Current Statistics:")
    stats = tracker.get_statistics()

    print(f"\n   Bandwidth: {stats['total_bandwidth_mb']:.2f} MB ({stats['total_bandwidth_gb']:.3f} GB)")
    print(f"   Runtime: {stats['uptime_hours']:.2f} hours")
    print(f"   Products: {stats['successful_products']:,} successful, {stats['failed_products']:,} failed")
    print(f"\n   Proxy Cost: ${stats['proxy_cost_usd']:.2f}")
    print(f"   Server Cost: ${stats['server_cost_usd']:.2f}")
    print(f"   Total Cost: ${stats['total_cost_usd']:.2f}")
    print(f"   Cost per Product: ${stats['cost_per_product_usd']:.4f}")

    # Test estimation
    print("\n4. Estimating cost for 1,500,000 products...")
    estimate = tracker.estimate_total_cost(1500000)

    if 'error' not in estimate:
        print(f"\n   Completion: {estimate['completion_percent']:.2f}%")
        print(f"   Days Remaining: {estimate['days_remaining']:.1f}")
        print(f"   Estimated Total Cost: ${estimate['estimated_total_cost_usd']:.2f}")
        print(f"   Cost per Product: ${estimate['cost_per_product']:.4f}")

    # Export report
    print("\n5. Exporting report...")
    tracker.export_report("/tmp/cost_tracker_test_report.json")
    print("   Report exported to /tmp/cost_tracker_test_report.json")

    # Print summary
    print("\n6. Summary Text:")
    print(tracker.get_summary_text())

    print("\n✅ Cost tracker test completed")
