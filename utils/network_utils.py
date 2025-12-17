#!/usr/bin/env python3
"""
Network Monitoring and Outage Detection for MRO Supply Scraper
Detects network issues and manages automatic pause/resume
"""

import time
import logging
import requests
from datetime import datetime
from typing import Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """
    Monitor network connectivity and handle outages

    Features:
    - Detect connection failures
    - Automatic pause on outage
    - Periodic connectivity checks
    - Resume when network returns
    """

    def __init__(self, config, notifier=None):
        """
        Initialize network monitor

        Args:
            config: Configuration object
            notifier: Optional notifier for alerts
        """
        self.config = config
        self.notifier = notifier

        # Network status
        self.is_connected = True
        self.outage_start_time = None
        self.last_check_time = 0
        self.consecutive_failures = 0

        # History tracking
        self.connectivity_history = deque(maxlen=100)  # Last 100 checks

        # Configuration
        self.check_interval = 60  # Check every 60 seconds during outage
        self.max_outage_duration = 3600  # 1 hour max wait
        self.failure_threshold = 3  # Consider offline after 3 consecutive failures
        self.check_urls = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://1.1.1.1"
        ]

        logger.info("Network monitor initialized")

    def check_connectivity(self, quick: bool = False) -> bool:
        """
        Check if network is available

        Args:
            quick: If True, use shorter timeout for faster check

        Returns:
            bool: True if connected, False if offline
        """
        timeout = 5 if quick else 10

        # Try multiple reliable endpoints
        for url in self.check_urls:
            try:
                response = requests.get(
                    url,
                    timeout=timeout,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )

                if response.status_code in [200, 301, 302]:
                    # Success - network is available
                    self._record_check(True)
                    return True

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                # Try next URL
                logger.debug(f"Failed to reach {url}: {e}")
                continue

        # All checks failed
        self._record_check(False)
        return False

    def _record_check(self, success: bool):
        """Record connectivity check result"""
        self.connectivity_history.append({
            'time': time.time(),
            'success': success,
            'timestamp': datetime.now()
        })

        if success:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

    def handle_connection_error(self, error: Exception) -> bool:
        """
        Handle connection error from scraper

        Args:
            error: The exception that was raised

        Returns:
            bool: True if should retry, False if should give up
        """
        # Increment failure counter
        self.consecutive_failures += 1

        logger.warning(
            f"Connection error #{self.consecutive_failures}: {error}"
        )

        # Check if we should consider network offline
        if self.consecutive_failures >= self.failure_threshold:
            if self.is_connected:
                # Network just went down
                logger.error("Network appears to be offline")
                self._handle_network_outage()

            # Check if we should give up
            if self.outage_start_time:
                outage_duration = time.time() - self.outage_start_time

                if outage_duration > self.max_outage_duration:
                    logger.critical(
                        f"Network outage exceeded max duration "
                        f"({self.max_outage_duration}s)"
                    )
                    self._send_critical_alert(outage_duration)
                    return False  # Give up

            # Wait and check connectivity
            return self._wait_for_network_recovery()

        # Just a transient error, retry
        return True

    def _handle_network_outage(self):
        """Handle network outage detected"""
        self.is_connected = False
        self.outage_start_time = time.time()

        logger.error("=" * 60)
        logger.error("NETWORK OUTAGE DETECTED")
        logger.error("Pausing scraper and monitoring connectivity")
        logger.error("=" * 60)

        # Send alert
        if self.notifier:
            self.notifier.send_alert(
                "Network outage detected",
                {
                    "consecutive_failures": self.consecutive_failures,
                    "time": datetime.now().isoformat(),
                    "action": "Scraper paused, monitoring connectivity"
                }
            )

    def _wait_for_network_recovery(self) -> bool:
        """
        Wait for network to recover

        Returns:
            bool: True if network recovered, False if timeout
        """
        logger.info("Waiting for network recovery...")

        while True:
            # Check if max duration exceeded
            if self.outage_start_time:
                outage_duration = time.time() - self.outage_start_time

                if outage_duration > self.max_outage_duration:
                    logger.critical("Max outage duration exceeded")
                    return False

                logger.info(
                    f"Network outage: {outage_duration:.0f}s / "
                    f"{self.max_outage_duration}s"
                )

            # Check connectivity
            if self.check_connectivity(quick=True):
                # Network is back!
                self._handle_network_recovery()
                return True

            # Wait before next check
            logger.info(f"Still offline, checking again in {self.check_interval}s")
            time.sleep(self.check_interval)

    def _handle_network_recovery(self):
        """Handle network recovery"""
        if not self.is_connected:
            outage_duration = time.time() - self.outage_start_time if self.outage_start_time else 0

            logger.info("=" * 60)
            logger.info("NETWORK RECOVERED")
            logger.info(f"Outage duration: {outage_duration:.0f} seconds")
            logger.info("Resuming scraper")
            logger.info("=" * 60)

            # Send notification
            if self.notifier:
                self.notifier.send_alert(
                    "Network recovered",
                    {
                        "outage_duration_seconds": outage_duration,
                        "outage_duration_minutes": outage_duration / 60,
                        "recovery_time": datetime.now().isoformat(),
                        "action": "Resuming scraper"
                    }
                )

        # Reset state
        self.is_connected = True
        self.outage_start_time = None
        self.consecutive_failures = 0

    def _send_critical_alert(self, outage_duration: float):
        """Send critical alert for extended outage"""
        if not self.notifier:
            return

        self.notifier.send_critical_alert(
            "Extended network outage - scraper stopped",
            {
                "outage_duration_minutes": outage_duration / 60,
                "outage_duration_hours": outage_duration / 3600,
                "max_duration_minutes": self.max_outage_duration / 60,
                "time": datetime.now().isoformat(),
                "consecutive_failures": self.consecutive_failures,
                "action": "Scraper stopped - manual intervention required"
            }
        )

    def get_connectivity_stats(self) -> dict:
        """
        Get connectivity statistics

        Returns:
            dict: Connectivity statistics
        """
        if not self.connectivity_history:
            return {
                'total_checks': 0,
                'success_count': 0,
                'failure_count': 0,
                'success_rate': 0,
                'is_connected': self.is_connected
            }

        total = len(self.connectivity_history)
        success_count = sum(1 for c in self.connectivity_history if c['success'])
        failure_count = total - success_count

        stats = {
            'total_checks': total,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': (success_count / total * 100) if total > 0 else 0,
            'is_connected': self.is_connected,
            'consecutive_failures': self.consecutive_failures
        }

        # Add outage info if currently offline
        if not self.is_connected and self.outage_start_time:
            stats['outage_duration_seconds'] = time.time() - self.outage_start_time
            stats['outage_duration_minutes'] = stats['outage_duration_seconds'] / 60

        return stats

    def is_network_available(self) -> bool:
        """
        Check if network is currently available

        Returns:
            bool: True if network is available
        """
        return self.is_connected

    def reset_failure_counter(self):
        """Reset consecutive failure counter"""
        self.consecutive_failures = 0

    def periodic_check(self):
        """
        Perform periodic connectivity check

        Should be called regularly from main loop
        """
        # Only check periodically to avoid overhead
        current_time = time.time()

        if current_time - self.last_check_time < 300:  # 5 minutes
            return

        self.last_check_time = current_time

        # Quick connectivity check
        is_online = self.check_connectivity(quick=True)

        if not is_online and self.is_connected:
            logger.warning("Periodic check detected network issue")
            self._handle_network_outage()
        elif is_online and not self.is_connected:
            logger.info("Periodic check detected network recovery")
            self._handle_network_recovery()


class ConnectionErrorHandler:
    """
    Helper class to handle connection errors with retry logic
    """

    def __init__(self, network_monitor: NetworkMonitor, max_retries: int = 3):
        """
        Initialize connection error handler

        Args:
            network_monitor: NetworkMonitor instance
            max_retries: Maximum retry attempts
        """
        self.network_monitor = network_monitor
        self.max_retries = max_retries

    def handle_request_error(self, error: Exception, attempt: int = 1) -> Tuple[bool, Optional[float]]:
        """
        Handle request error with retry logic

        Args:
            error: The exception that was raised
            attempt: Current attempt number

        Returns:
            Tuple[bool, Optional[float]]: (should_retry, delay_seconds)
        """
        # Check error type
        if isinstance(error, (requests.exceptions.ConnectionError,
                             requests.exceptions.Timeout)):
            # Network-related error
            logger.warning(f"Network error on attempt {attempt}/{self.max_retries}: {error}")

            # Let network monitor handle it
            should_continue = self.network_monitor.handle_connection_error(error)

            if not should_continue:
                return False, None  # Give up

            if attempt >= self.max_retries:
                return False, None  # Max retries reached

            # Calculate exponential backoff
            delay = min(2 ** attempt, 60)  # Max 60 seconds
            return True, delay

        # Other error types (not network-related)
        return False, None


def is_network_error(error: Exception) -> bool:
    """
    Check if error is network-related

    Args:
        error: Exception to check

    Returns:
        bool: True if network-related error
    """
    return isinstance(error, (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        ConnectionError,
        TimeoutError
    ))


if __name__ == '__main__':
    # Test network monitor
    import sys
    sys.path.insert(0, '.')
    from config import Config
    from notifier import Notifier

    try:
        config = Config()
        notifier = Notifier(config)
        monitor = NetworkMonitor(config, notifier)

        print("Network Monitor Test")
        print("=" * 60)

        # Test connectivity
        print("\n1. Testing connectivity...")
        is_online = monitor.check_connectivity()
        print(f"   Result: {'Online ✓' if is_online else 'Offline ✗'}")

        # Get stats
        print("\n2. Connectivity statistics:")
        stats = monitor.get_connectivity_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Test simulated outage
        print("\n3. Simulating connection error...")
        monitor.handle_connection_error(
            requests.exceptions.ConnectionError("Simulated error")
        )

        print("\n✅ Network monitor test completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
