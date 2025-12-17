#!/usr/bin/env python3
"""
Disk Space Monitor and Auto-Cleanup for MRO Supply Scraper
Monitors disk usage and performs automatic cleanup when needed
"""

import shutil
import gzip
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)


class DiskMonitor:
    """Disk space monitoring and management"""

    def __init__(self, config, notifier=None):
        """Initialize disk monitor"""
        self.config = config
        self.notifier = notifier
        self.cleanup_actions = [
            self.compress_old_logs,
            self.delete_old_checkpoints,
            self.delete_temp_files
        ]

    def check_disk_space(self) -> Tuple[float, bool]:
        """
        Check available disk space

        Returns:
            (free_gb, is_critical): Free space in GB and whether it's critical
        """
        try:
            stats = shutil.disk_usage(str(self.config.OUTPUT_DIR))
            free_gb = stats.free / (1024**3)
            total_gb = stats.total / (1024**3)
            used_percent = (stats.used / stats.total) * 100

            threshold = self.config.DISK_SPACE_THRESHOLD_GB
            is_critical = free_gb < threshold

            if is_critical:
                logger.warning(
                    f"Low disk space: {free_gb:.1f}GB free "
                    f"({100-used_percent:.1f}% available) - threshold: {threshold}GB"
                )
            else:
                logger.info(
                    f"Disk space OK: {free_gb:.1f}GB free "
                    f"({100-used_percent:.1f}% available)"
                )

            return free_gb, is_critical

        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return 0.0, True

    def auto_cleanup(self) -> float:
        """
        Automatically free up disk space

        Returns:
            float: Bytes freed
        """
        logger.info("Starting automatic disk cleanup")

        freed_space = 0

        for action in self.cleanup_actions:
            try:
                action_name = action.__name__
                logger.info(f"Running cleanup action: {action_name}")

                space = action()
                freed_space += space

                if space > 0:
                    logger.info(f"{action_name} freed {space/1024/1024:.1f}MB")

            except Exception as e:
                logger.error(f"Cleanup action {action.__name__} failed: {e}")

        total_mb = freed_space / 1024 / 1024
        logger.info(f"Total space freed: {total_mb:.1f}MB")

        # Send notification
        if self.notifier:
            self.notifier.send_alert(
                "Disk cleanup completed",
                {"freed_mb": total_mb}
            )

        return freed_space

    def compress_old_logs(self) -> int:
        """
        Compress log files older than 24 hours

        Returns:
            int: Bytes freed
        """
        freed = 0

        try:
            # Check both main directory and log directory
            search_dirs = [
                self.config.OUTPUT_DIR,
                self.config.LOG_DIR
            ]

            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue

                for log_file in search_dir.glob("*.log"):
                    try:
                        # Skip if already compressed
                        if log_file.suffix == '.gz':
                            continue

                        # Check age
                        age_hours = (time.time() - log_file.stat().st_mtime) / 3600

                        if age_hours > 24:
                            original_size = log_file.stat().st_size

                            # Compress with gzip
                            gz_file = Path(str(log_file) + '.gz')
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(gz_file, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)

                            # Delete original
                            log_file.unlink()

                            # Calculate space saved
                            new_size = gz_file.stat().st_size
                            saved = original_size - new_size
                            freed += saved

                            logger.info(
                                f"Compressed {log_file.name}: "
                                f"{original_size/1024:.1f}KB -> {new_size/1024:.1f}KB "
                                f"(saved {saved/1024:.1f}KB)"
                            )

                    except Exception as e:
                        logger.error(f"Failed to compress {log_file}: {e}")

        except Exception as e:
            logger.error(f"Error in compress_old_logs: {e}")

        return freed

    def delete_old_checkpoints(self) -> int:
        """
        Delete old checkpoint files, keep last 3

        Returns:
            int: Bytes freed
        """
        freed = 0

        try:
            checkpoint_dir = self.config.OUTPUT_DIR

            # Find all checkpoint files (including timestamped backups)
            checkpoints = []

            # Regular checkpoint
            regular = checkpoint_dir / "checkpoint_products.json"
            if regular.exists():
                checkpoints.append(regular)

            # Timestamped checkpoints
            for cp in checkpoint_dir.glob("checkpoint_products_*.json"):
                checkpoints.append(cp)

            # Sort by modification time (newest first)
            checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Keep newest 3, delete rest
            for old_checkpoint in checkpoints[3:]:
                try:
                    size = old_checkpoint.stat().st_size
                    old_checkpoint.unlink()
                    freed += size
                    logger.info(f"Deleted old checkpoint: {old_checkpoint.name} ({size/1024:.1f}KB)")

                except Exception as e:
                    logger.error(f"Failed to delete checkpoint {old_checkpoint}: {e}")

        except Exception as e:
            logger.error(f"Error in delete_old_checkpoints: {e}")

        return freed

    def delete_temp_files(self) -> int:
        """
        Delete temporary files

        Returns:
            int: Bytes freed
        """
        freed = 0

        try:
            # Common temp file patterns
            temp_patterns = [
                "*.tmp",
                "*.temp",
                "*~",
                ".DS_Store",
                "Thumbs.db"
            ]

            for pattern in temp_patterns:
                for temp_file in self.config.OUTPUT_DIR.rglob(pattern):
                    try:
                        size = temp_file.stat().st_size
                        temp_file.unlink()
                        freed += size
                        logger.info(f"Deleted temp file: {temp_file.name}")

                    except Exception as e:
                        logger.error(f"Failed to delete temp file {temp_file}: {e}")

        except Exception as e:
            logger.error(f"Error in delete_temp_files: {e}")

        return freed

    def estimate_disk_usage(self, total_products: int) -> float:
        """
        Estimate total disk space needed for scraping

        Args:
            total_products: Total number of products to scrape

        Returns:
            float: Estimated disk usage in GB
        """
        # Rough estimates based on typical data sizes
        avg_product_size = 2048  # bytes per product in JSON
        checkpoint_size = total_products * avg_product_size
        log_size = total_products * 100  # bytes per log entry
        error_size = total_products * 0.05 * 200  # 5% failure rate estimate

        total_estimated = (checkpoint_size + log_size + error_size) * 1.2  # 20% buffer

        return total_estimated / (1024**3)  # Convert to GB

    def get_disk_stats(self) -> dict:
        """
        Get detailed disk statistics

        Returns:
            dict: Disk statistics
        """
        try:
            stats = shutil.disk_usage(str(self.config.OUTPUT_DIR))

            return {
                'total_gb': stats.total / (1024**3),
                'used_gb': stats.used / (1024**3),
                'free_gb': stats.free / (1024**3),
                'used_percent': (stats.used / stats.total) * 100,
                'threshold_gb': self.config.DISK_SPACE_THRESHOLD_GB,
                'is_critical': stats.free / (1024**3) < self.config.DISK_SPACE_THRESHOLD_GB
            }

        except Exception as e:
            logger.error(f"Error getting disk stats: {e}")
            return {}

    def monitor_and_cleanup(self):
        """Monitor disk space and perform cleanup if needed"""
        free_gb, is_critical = self.check_disk_space()

        if is_critical:
            logger.warning("Disk space critical, starting automatic cleanup")

            if self.notifier:
                self.notifier.send_alert(
                    f"Low disk space: {free_gb:.1f}GB",
                    {"free_gb": free_gb, "threshold_gb": self.config.DISK_SPACE_THRESHOLD_GB}
                )

            # Perform cleanup
            freed_bytes = self.auto_cleanup()

            # Check again
            free_gb_after, still_critical = self.check_disk_space()

            if still_critical:
                logger.error(
                    f"Disk space still critical after cleanup: {free_gb_after:.1f}GB free"
                )
                if self.notifier:
                    self.notifier.send_critical_alert(
                        "Disk space critically low even after cleanup",
                        {
                            "free_gb": free_gb_after,
                            "freed_mb": freed_bytes / 1024 / 1024,
                            "threshold_gb": self.config.DISK_SPACE_THRESHOLD_GB
                        }
                    )
            else:
                logger.info(f"Cleanup successful: {free_gb_after:.1f}GB free")


if __name__ == '__main__':
    # Test disk monitor
    import sys
    import argparse
    sys.path.insert(0, '.')
    from config import Config
    from notifier import Notifier

    parser = argparse.ArgumentParser(description='Disk Space Monitor')
    parser.add_argument('--check', action='store_true', help='Check disk space')
    parser.add_argument('--cleanup', action='store_true', help='Perform cleanup')
    parser.add_argument('--monitor', action='store_true', help='Monitor and cleanup if needed')
    args = parser.parse_args()

    try:
        config = Config()
        notifier = Notifier(config)
        monitor = DiskMonitor(config, notifier)

        if args.check or (not args.cleanup and not args.monitor):
            # Just check
            free_gb, is_critical = monitor.check_disk_space()
            stats = monitor.get_disk_stats()

            print("\nDisk Space Status:")
            print("=" * 50)
            print(f"Total: {stats['total_gb']:.1f} GB")
            print(f"Used: {stats['used_gb']:.1f} GB ({stats['used_percent']:.1f}%)")
            print(f"Free: {stats['free_gb']:.1f} GB")
            print(f"Threshold: {stats['threshold_gb']:.1f} GB")
            print(f"Status: {'🚨 CRITICAL' if is_critical else '✅ OK'}")

        if args.cleanup:
            # Force cleanup
            print("\nPerforming cleanup...")
            freed = monitor.auto_cleanup()
            print(f"✅ Freed {freed/1024/1024:.1f} MB")

        if args.monitor:
            # Monitor and cleanup if needed
            print("\nMonitoring disk space...")
            monitor.monitor_and_cleanup()
            print("✅ Monitoring complete")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
