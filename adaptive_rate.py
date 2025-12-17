#!/usr/bin/env python3
"""
Adaptive Rate Limiter for MRO Supply Scraper
Dynamically adjusts request rate based on success metrics
"""

import time
import logging
from typing import Dict, Optional
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """
    Dynamically adjust scraping rate based on performance

    Strategy:
    - Monitor success rate over last 100 requests
    - If success < 85% → Slow down (increase delay 25%, reduce workers 10%)
    - If success > 95% → Speed up (decrease delay 10%, increase workers 5%)
    - Adjustment interval: Minimum 5 minutes
    - Cap workers at 150% of original
    - Cautious speed increases, aggressive slowdowns
    """

    # Thresholds
    SLOW_DOWN_THRESHOLD = 0.85  # 85%
    SPEED_UP_THRESHOLD = 0.95   # 95%

    # Adjustment amounts
    SLOWDOWN_DELAY_INCREASE = 0.25    # +25%
    SLOWDOWN_WORKER_DECREASE = 0.10   # -10%
    SPEEDUP_DELAY_DECREASE = 0.10     # -10%
    SPEEDUP_WORKER_INCREASE = 0.05    # +5%

    # Limits
    MIN_ADJUSTMENT_INTERVAL = 300  # 5 minutes
    MAX_WORKER_MULTIPLIER = 1.5    # 150% of original
    MIN_WORKER_COUNT = 1
    MIN_DELAY = 0.1                # 100ms minimum
    MAX_DELAY = 5.0                # 5s maximum

    # Sample size
    SAMPLE_SIZE = 100

    def __init__(self, initial_delay: float, initial_workers: int, config=None):
        """
        Initialize adaptive rate limiter

        Args:
            initial_delay: Initial delay between requests (seconds)
            initial_workers: Initial worker count
            config: Optional configuration object
        """
        self.config = config

        # Initial settings (immutable)
        self.initial_delay = initial_delay
        self.initial_workers = initial_workers

        # Current settings (mutable)
        self.current_delay = initial_delay
        self.current_workers = initial_workers

        # Request history (success/failure)
        self.request_history = deque(maxlen=self.SAMPLE_SIZE)

        # Adjustment tracking
        self.last_adjustment_time = time.time()
        self.adjustment_count = 0
        self.slowdown_count = 0
        self.speedup_count = 0

        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        logger.info(
            f"Adaptive rate limiter initialized: "
            f"delay={initial_delay}s, workers={initial_workers}"
        )

    def record_request(self, success: bool):
        """
        Record request result

        Args:
            success: Whether request was successful
        """
        self.request_history.append({
            'success': success,
            'timestamp': time.time()
        })

        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

    def should_adjust(self) -> bool:
        """Check if enough time has passed for adjustment"""
        elapsed = time.time() - self.last_adjustment_time
        return elapsed >= self.MIN_ADJUSTMENT_INTERVAL

    def calculate_success_rate(self) -> Optional[float]:
        """
        Calculate recent success rate

        Returns:
            Success rate (0-1) or None if insufficient data
        """
        if len(self.request_history) < 10:
            # Need minimum sample
            return None

        successes = sum(1 for r in self.request_history if r['success'])
        return successes / len(self.request_history)

    def adjust_rate(self) -> bool:
        """
        Adjust rate based on recent performance

        Returns:
            bool: True if adjustment made, False otherwise
        """
        # Check if should adjust
        if not self.should_adjust():
            return False

        # Calculate success rate
        success_rate = self.calculate_success_rate()

        if success_rate is None:
            logger.debug("Insufficient data for rate adjustment")
            return False

        # Determine action
        if success_rate < self.SLOW_DOWN_THRESHOLD:
            # Performance poor - slow down
            self._slow_down(success_rate)
            return True

        elif success_rate > self.SPEED_UP_THRESHOLD:
            # Performance excellent - speed up
            self._speed_up(success_rate)
            return True

        else:
            # Performance acceptable - no change
            logger.debug(
                f"Rate adjustment check: success rate {success_rate:.1%} is acceptable"
            )
            return False

    def _slow_down(self, success_rate: float):
        """Slow down scraping rate"""
        old_delay = self.current_delay
        old_workers = self.current_workers

        # Increase delay (aggressive)
        self.current_delay *= (1 + self.SLOWDOWN_DELAY_INCREASE)
        self.current_delay = min(self.current_delay, self.MAX_DELAY)

        # Reduce workers (aggressive)
        new_workers = int(self.current_workers * (1 - self.SLOWDOWN_WORKER_DECREASE))
        self.current_workers = max(new_workers, self.MIN_WORKER_COUNT)

        # Update tracking
        self.last_adjustment_time = time.time()
        self.adjustment_count += 1
        self.slowdown_count += 1

        logger.warning(
            f"🐌 SLOWING DOWN due to low success rate ({success_rate:.1%}): "
            f"delay {old_delay:.2f}s → {self.current_delay:.2f}s, "
            f"workers {old_workers} → {self.current_workers}"
        )

    def _speed_up(self, success_rate: float):
        """Speed up scraping rate"""
        # Check if at maximum workers
        max_workers = int(self.initial_workers * self.MAX_WORKER_MULTIPLIER)

        if self.current_workers >= max_workers and self.current_delay <= self.MIN_DELAY:
            logger.debug(
                f"Already at maximum rate (workers={max_workers}, "
                f"delay={self.MIN_DELAY}s)"
            )
            return

        old_delay = self.current_delay
        old_workers = self.current_workers

        # Decrease delay (cautious)
        self.current_delay *= (1 - self.SPEEDUP_DELAY_DECREASE)
        self.current_delay = max(self.current_delay, self.MIN_DELAY)

        # Increase workers (cautious)
        new_workers = int(self.current_workers * (1 + self.SPEEDUP_WORKER_INCREASE))
        self.current_workers = min(new_workers, max_workers)

        # Update tracking
        self.last_adjustment_time = time.time()
        self.adjustment_count += 1
        self.speedup_count += 1

        logger.info(
            f"🚀 SPEEDING UP due to high success rate ({success_rate:.1%}): "
            f"delay {old_delay:.2f}s → {self.current_delay:.2f}s, "
            f"workers {old_workers} → {self.current_workers}"
        )

    def get_current_settings(self) -> Dict:
        """
        Get current rate settings

        Returns:
            dict: Current settings
        """
        return {
            'delay': self.current_delay,
            'workers': self.current_workers
        }

    def get_statistics(self) -> Dict:
        """
        Get adaptive rate statistics

        Returns:
            dict: Statistics
        """
        success_rate = self.calculate_success_rate()

        stats = {
            'current_delay': round(self.current_delay, 3),
            'current_workers': self.current_workers,
            'initial_delay': self.initial_delay,
            'initial_workers': self.initial_workers,
            'delay_change_percent': (
                ((self.current_delay - self.initial_delay) / self.initial_delay * 100)
                if self.initial_delay > 0 else 0
            ),
            'worker_change_percent': (
                ((self.current_workers - self.initial_workers) / self.initial_workers * 100)
                if self.initial_workers > 0 else 0
            ),
            'recent_success_rate': (
                round(success_rate * 100, 2)
                if success_rate is not None else None
            ),
            'overall_success_rate': (
                round((self.successful_requests / self.total_requests * 100), 2)
                if self.total_requests > 0 else 0
            ),
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'adjustment_count': self.adjustment_count,
            'slowdown_count': self.slowdown_count,
            'speedup_count': self.speedup_count,
            'sample_size': len(self.request_history),
            'time_since_last_adjustment': round(
                time.time() - self.last_adjustment_time, 0
            )
        }

        return stats

    def reset_to_initial(self):
        """Reset to initial settings"""
        logger.info(
            f"Resetting to initial settings: "
            f"delay={self.initial_delay}s, workers={self.initial_workers}"
        )

        self.current_delay = self.initial_delay
        self.current_workers = self.initial_workers

    def force_slow_mode(self):
        """Force slow mode (useful during rate limiting)"""
        logger.warning("Forcing slow mode")

        self.current_delay = self.MAX_DELAY
        self.current_workers = self.MIN_WORKER_COUNT
        self.last_adjustment_time = time.time()

    def is_at_max_speed(self) -> bool:
        """Check if operating at maximum speed"""
        max_workers = int(self.initial_workers * self.MAX_WORKER_MULTIPLIER)
        return (
            self.current_workers >= max_workers and
            self.current_delay <= self.MIN_DELAY
        )

    def is_slower_than_initial(self) -> bool:
        """Check if currently slower than initial settings"""
        return (
            self.current_delay > self.initial_delay or
            self.current_workers < self.initial_workers
        )

    def get_performance_summary(self) -> str:
        """Get human-readable performance summary"""
        stats = self.get_statistics()

        delay_change = stats['delay_change_percent']
        worker_change = stats['worker_change_percent']
        success_rate = stats.get('recent_success_rate', 0)

        if self.is_at_max_speed():
            status = "🚀 MAX SPEED"
        elif self.is_slower_than_initial():
            status = "🐌 THROTTLED"
        else:
            status = "✓ NORMAL"

        summary = (
            f"{status} | "
            f"Delay: {self.current_delay:.2f}s ({delay_change:+.0f}%) | "
            f"Workers: {self.current_workers} ({worker_change:+.0f}%) | "
            f"Success: {success_rate:.1f}%"
        )

        return summary


if __name__ == '__main__':
    # Test adaptive rate limiter
    import random

    print("Adaptive Rate Limiter Test")
    print("=" * 60)

    # Initialize with moderate settings
    limiter = AdaptiveRateLimiter(
        initial_delay=0.5,
        initial_workers=20
    )

    print(f"\nInitial settings: {limiter.get_current_settings()}")

    # Simulate requests with varying success rates
    print("\n1. Simulating 50 requests with 95% success (should speed up)...")
    for i in range(50):
        success = random.random() < 0.95
        limiter.record_request(success)

    # Try to adjust (won't work yet - need 5 minutes)
    print("   Attempting adjustment...")
    adjusted = limiter.adjust_rate()
    print(f"   Adjusted: {adjusted} (need to wait 5 minutes)")

    # Force adjustment for testing
    limiter.last_adjustment_time = time.time() - 301
    adjusted = limiter.adjust_rate()
    print(f"   Forced adjustment: {adjusted}")
    print(f"   New settings: {limiter.get_current_settings()}")

    # Simulate poor performance
    print("\n2. Simulating 50 requests with 70% success (should slow down)...")
    for i in range(50):
        success = random.random() < 0.70
        limiter.record_request(success)

    limiter.last_adjustment_time = time.time() - 301
    adjusted = limiter.adjust_rate()
    print(f"   Adjusted: {adjusted}")
    print(f"   New settings: {limiter.get_current_settings()}")

    # Show statistics
    print("\n3. Statistics:")
    stats = limiter.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Show summary
    print(f"\n4. Performance Summary:")
    print(f"   {limiter.get_performance_summary()}")

    print("\n✅ Adaptive rate limiter test completed")
