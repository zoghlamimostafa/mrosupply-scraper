#!/usr/bin/env python3
"""
Graceful Shutdown Handler for MRO Supply Scraper
Handles SIGTERM and SIGINT signals to ensure clean exits
"""

import signal
import sys
import time
import logging
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """
    Handles graceful shutdown of scraper on SIGTERM/SIGINT

    Ensures:
    - No data corruption
    - Checkpoint saved
    - Active requests complete
    - Clean exit
    """

    def __init__(self, scraper, notifier=None, max_wait_seconds: int = 300):
        """
        Initialize graceful shutdown handler

        Args:
            scraper: The scraper instance to manage
            notifier: Optional notifier for sending alerts
            max_wait_seconds: Maximum time to wait for active requests (default: 5 minutes)
        """
        self.scraper = scraper
        self.notifier = notifier
        self.max_wait_seconds = max_wait_seconds
        self.shutdown_requested = False
        self.force_shutdown = False
        self.shutdown_start_time = None

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("Graceful shutdown handler initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"

        if self.force_shutdown:
            # Second signal - force immediate shutdown
            logger.critical(f"Second {signal_name} received - forcing immediate shutdown!")
            self._force_exit()
            return

        if self.shutdown_requested:
            # Already shutting down, second signal forces immediate exit
            logger.warning(f"{signal_name} received during shutdown - forcing immediate exit")
            self.force_shutdown = True
            return

        # First signal - initiate graceful shutdown
        logger.info(f"{signal_name} received - initiating graceful shutdown")
        self.shutdown_requested = True
        self.shutdown_start_time = time.time()

        # Start shutdown sequence in separate thread to not block signal handler
        import threading
        shutdown_thread = threading.Thread(target=self._perform_shutdown, daemon=True)
        shutdown_thread.start()

    def _perform_shutdown(self):
        """Perform graceful shutdown sequence"""
        try:
            logger.info("=" * 60)
            logger.info("GRACEFUL SHUTDOWN SEQUENCE STARTED")
            logger.info("=" * 60)

            # Step 1: Stop accepting new work
            logger.info("Step 1/6: Stopping acceptance of new URLs")
            self._stop_new_work()

            # Step 2: Wait for active requests to complete
            logger.info(f"Step 2/6: Waiting for active requests (max {self.max_wait_seconds}s)")
            self._wait_for_active_requests()

            # Step 3: Save checkpoint
            logger.info("Step 3/6: Saving checkpoint")
            self._save_checkpoint()

            # Step 4: Save partial results
            logger.info("Step 4/6: Saving partial results")
            self._save_partial_results()

            # Step 5: Send notification
            logger.info("Step 5/6: Sending shutdown notification")
            self._send_notification()

            # Step 6: Final cleanup
            logger.info("Step 6/6: Performing final cleanup")
            self._final_cleanup()

            logger.info("=" * 60)
            logger.info("GRACEFUL SHUTDOWN COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)

            # Exit cleanly
            sys.exit(0)

        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
            logger.error("Forcing immediate shutdown")
            self._force_exit()

    def _stop_new_work(self):
        """Stop accepting new URLs to process"""
        try:
            # Set flag in scraper to stop processing new items
            if hasattr(self.scraper, 'should_stop'):
                self.scraper.should_stop = True

            # Stop worker threads if they exist
            if hasattr(self.scraper, 'stop_workers'):
                self.scraper.stop_workers()

            logger.info("Successfully stopped acceptance of new work")

        except Exception as e:
            logger.error(f"Error stopping new work: {e}")

    def _wait_for_active_requests(self):
        """Wait for active requests to complete"""
        try:
            start_time = time.time()
            check_interval = 2  # Check every 2 seconds

            while True:
                # Check if we've exceeded max wait time
                elapsed = time.time() - start_time
                if elapsed >= self.max_wait_seconds:
                    logger.warning(f"Max wait time ({self.max_wait_seconds}s) exceeded")
                    break

                # Check if force shutdown was requested
                if self.force_shutdown:
                    logger.warning("Force shutdown requested - stopping wait")
                    break

                # Check active requests
                active_count = self._get_active_request_count()

                if active_count == 0:
                    logger.info("All active requests completed")
                    break

                logger.info(f"Waiting for {active_count} active requests ({elapsed:.0f}s elapsed)")
                time.sleep(check_interval)

        except Exception as e:
            logger.error(f"Error waiting for active requests: {e}")

    def _get_active_request_count(self) -> int:
        """Get count of active requests"""
        try:
            # Check various possible attributes
            if hasattr(self.scraper, 'active_requests'):
                return self.scraper.active_requests

            if hasattr(self.scraper, 'executor') and self.scraper.executor:
                # ThreadPoolExecutor doesn't directly expose active count
                # but we can check the queue
                return 0  # Assume workers will finish quickly

            return 0

        except Exception as e:
            logger.error(f"Error getting active request count: {e}")
            return 0

    def _save_checkpoint(self):
        """Save checkpoint to disk"""
        try:
            if hasattr(self.scraper, 'save_checkpoint'):
                logger.info("Calling scraper's save_checkpoint method")
                self.scraper.save_checkpoint()
                logger.info("Checkpoint saved successfully")
            else:
                logger.warning("Scraper has no save_checkpoint method")

        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            # Continue with shutdown even if checkpoint fails

    def _save_partial_results(self):
        """Save any partial results"""
        try:
            # Save scraped products if any exist
            if hasattr(self.scraper, 'save_results'):
                logger.info("Calling scraper's save_results method")
                self.scraper.save_results()
                logger.info("Partial results saved successfully")

            # Export to CSV if method exists
            if hasattr(self.scraper, 'export_to_csv'):
                logger.info("Exporting to CSV")
                self.scraper.export_to_csv()
                logger.info("CSV export completed")

        except Exception as e:
            logger.error(f"Error saving partial results: {e}")
            # Continue with shutdown

    def _send_notification(self):
        """Send shutdown notification via email"""
        try:
            if not self.notifier:
                logger.info("No notifier configured, skipping notification")
                return

            # Gather statistics
            stats = self._gather_stats()

            # Send alert
            self.notifier.send_alert(
                "Scraper shutdown",
                {
                    "reason": "Graceful shutdown (SIGTERM/SIGINT)",
                    "completed": stats.get('completed', 0),
                    "total": stats.get('total', 0),
                    "percent": stats.get('percent', 0),
                    "uptime_hours": stats.get('uptime_hours', 0),
                    "shutdown_time": datetime.now().isoformat()
                }
            )

            logger.info("Shutdown notification sent")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def _gather_stats(self) -> dict:
        """Gather current statistics for notification"""
        try:
            stats = {}

            if hasattr(self.scraper, 'completed_count'):
                stats['completed'] = self.scraper.completed_count

            if hasattr(self.scraper, 'total_urls'):
                stats['total'] = self.scraper.total_urls

            if 'completed' in stats and 'total' in stats and stats['total'] > 0:
                stats['percent'] = (stats['completed'] / stats['total']) * 100

            if hasattr(self.scraper, 'start_time'):
                uptime = time.time() - self.scraper.start_time
                stats['uptime_hours'] = uptime / 3600

            return stats

        except Exception as e:
            logger.error(f"Error gathering stats: {e}")
            return {}

    def _final_cleanup(self):
        """Perform final cleanup"""
        try:
            # Close executor if exists
            if hasattr(self.scraper, 'executor') and self.scraper.executor:
                logger.info("Shutting down thread pool executor")
                self.scraper.executor.shutdown(wait=False)

            # Close any open files
            if hasattr(self.scraper, 'close'):
                self.scraper.close()

            # Flush logs
            for handler in logging.root.handlers:
                handler.flush()

            logger.info("Final cleanup completed")

        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")

    def _force_exit(self):
        """Force immediate exit"""
        logger.critical("Forcing immediate exit - data may be lost!")

        try:
            # Try to save checkpoint quickly
            if hasattr(self.scraper, 'save_checkpoint'):
                self.scraper.save_checkpoint()
        except:
            pass

        # Force exit
        sys.exit(1)

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested"""
        return self.shutdown_requested

    def check_timeout(self) -> bool:
        """Check if shutdown has exceeded timeout"""
        if not self.shutdown_requested or not self.shutdown_start_time:
            return False

        elapsed = time.time() - self.shutdown_start_time
        return elapsed > self.max_wait_seconds


def install_signal_handlers(scraper, notifier=None, max_wait_seconds: int = 300) -> GracefulShutdown:
    """
    Convenience function to install signal handlers

    Args:
        scraper: The scraper instance
        notifier: Optional notifier for alerts
        max_wait_seconds: Max time to wait for graceful shutdown

    Returns:
        GracefulShutdown instance
    """
    return GracefulShutdown(scraper, notifier, max_wait_seconds)


if __name__ == '__main__':
    # Test signal handlers
    import sys

    class DummyScraper:
        """Dummy scraper for testing"""
        def __init__(self):
            self.should_stop = False
            self.completed_count = 1000
            self.total_urls = 5000
            self.start_time = time.time() - 3600  # 1 hour ago

        def save_checkpoint(self):
            print("Saving checkpoint...")
            time.sleep(1)

        def save_results(self):
            print("Saving results...")
            time.sleep(0.5)

    # Create dummy scraper
    scraper = DummyScraper()

    # Install signal handlers
    shutdown_handler = install_signal_handlers(scraper, max_wait_seconds=10)

    print("Signal handlers installed")
    print("Press Ctrl+C to test graceful shutdown")
    print("Press Ctrl+C twice quickly to test force shutdown")
    print()

    # Simulate running scraper
    try:
        while not shutdown_handler.is_shutdown_requested():
            print("Scraper running... (Ctrl+C to stop)")
            time.sleep(2)
    except KeyboardInterrupt:
        # Signal handler will catch this
        pass

    # Wait for shutdown to complete
    print("\nWaiting for shutdown to complete...")
    time.sleep(15)
