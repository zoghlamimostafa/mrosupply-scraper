#!/usr/bin/env python3
"""
Watchdog Process Supervisor for MRO Supply Scraper
Monitors scraper process and restarts on crash
"""

import sys
import time
import subprocess
import signal
import logging
from datetime import datetime
from pathlib import Path
from collections import deque

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperWatchdog:
    """Process supervisor for scraper"""

    def __init__(self, config):
        """Initialize watchdog"""
        self.config = config
        self.restart_count = 0
        self.restart_times = deque(maxlen=20)  # Track last 20 restart times
        self.process = None
        self.should_stop = False

        # Import notifier
        try:
            from notifier import Notifier
            self.notifier = Notifier(config)
        except Exception as e:
            logger.error(f"Failed to initialize notifier: {e}")
            self.notifier = None

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.should_stop = True
        if self.process:
            self.process.terminate()

    def start(self):
        """Start scraper with monitoring"""
        logger.info("Watchdog starting...")
        logger.info(f"Max restarts per hour: {self.config.MAX_RESTARTS_PER_HOUR}")
        logger.info(f"Max total restarts: {self.config.MAX_TOTAL_RESTARTS}")

        while not self.should_stop:
            try:
                # Start scraper process
                self.process = self.launch_scraper()

                if not self.process:
                    logger.error("Failed to launch scraper")
                    time.sleep(self.config.RESTART_DELAY_SECONDS)
                    continue

                logger.info(f"Scraper started with PID: {self.process.pid}")

                # Monitor process
                exit_code = self.process.wait()

                if self.should_stop:
                    logger.info("Watchdog shutdown requested, exiting")
                    break

                # Process died
                logger.warning(f"Scraper process exited with code: {exit_code}")

                # Handle crash
                should_restart = self.handle_crash(exit_code)

                if not should_restart:
                    logger.error("Max restart limit reached, watchdog stopping")
                    break

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                self.should_stop = True
                if self.process:
                    self.process.terminate()
                    self.process.wait(timeout=30)
                break

            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                time.sleep(10)

        logger.info("Watchdog stopped")

    def launch_scraper(self):
        """Launch scraper process"""
        try:
            # Build command
            cmd = [
                sys.executable,
                'scraper_rotating_residential.py',
                '--output-dir', str(self.config.OUTPUT_DIR),
                '--workers', str(self.config.WORKERS),
                '--delay', str(self.config.DELAY),
                '--resume'  # Always resume from checkpoint
            ]

            logger.info(f"Launching: {' '.join(cmd)}")

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            return process

        except Exception as e:
            logger.error(f"Failed to launch scraper: {e}")
            return None

    def handle_crash(self, exit_code: int) -> bool:
        """
        Handle scraper crash

        Returns:
            bool: True if should restart, False if giving up
        """
        self.restart_count += 1
        self.restart_times.append(time.time())

        logger.warning(f"Crash #{self.restart_count} (exit code: {exit_code})")

        # Check restart rate limits
        recent_restarts = [t for t in self.restart_times if time.time() - t < 3600]

        if len(recent_restarts) > self.config.MAX_RESTARTS_PER_HOUR:
            # Too many restarts in last hour
            msg = f"Too many crashes: {len(recent_restarts)} in last hour"
            logger.error(msg)

            if self.notifier:
                self.notifier.send_critical_alert(
                    "Scraper crashed too many times",
                    {
                        "restart_count": self.restart_count,
                        "recent_restarts": len(recent_restarts),
                        "exit_code": exit_code,
                        "time": datetime.now().isoformat()
                    }
                )

            # Wait longer before retry
            logger.info("Waiting 5 minutes before retry...")
            time.sleep(300)

        elif self.restart_count > self.config.MAX_TOTAL_RESTARTS:
            # Too many total restarts
            msg = f"Maximum total restarts exceeded: {self.restart_count}"
            logger.error(msg)

            if self.notifier:
                self.notifier.send_critical_alert(
                    "Maximum restart attempts exceeded",
                    {
                        "total_restarts": self.restart_count,
                        "exit_code": exit_code,
                        "time": datetime.now().isoformat()
                    }
                )

            return False  # Give up

        # Notify about restart
        if self.notifier:
            self.notifier.send_alert(
                f"Restarting scraper (attempt {self.restart_count})",
                {
                    "restart_count": self.restart_count,
                    "exit_code": exit_code,
                    "recent_restarts": len(recent_restarts)
                }
            )

        # Wait before restart
        delay = self.config.RESTART_DELAY_SECONDS
        logger.info(f"Waiting {delay} seconds before restart...")
        time.sleep(delay)

        return True


if __name__ == '__main__':
    try:
        # Load configuration
        from config import Config

        config = Config()

        if not config.WATCHDOG_ENABLED:
            logger.warning("Watchdog disabled in configuration")
            # Run scraper directly
            import scraper_rotating_residential
            sys.exit(0)

        # Start watchdog
        watchdog = ScraperWatchdog(config)
        watchdog.start()

    except Exception as e:
        logger.error(f"Watchdog failed: {e}")
        sys.exit(1)
