#!/usr/bin/env python3
"""
Configuration Management for MRO Supply Scraper
Loads settings from environment variables (.env file)
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class Config:
    """Configuration class with environment variable management"""

    def __init__(self):
        """Load and validate configuration from environment"""
        self._load_config()
        self._validate_required()

    def _load_config(self):
        """Load all configuration from environment variables"""

        # ============== Proxy Configuration ==============
        self.PROXY_HOST = os.getenv('PROXY_HOST', 'p.webshare.io')
        self.PROXY_PORT = int(os.getenv('PROXY_PORT', '10000'))
        self.PROXY_USER = os.getenv('PROXY_USER', '')
        self.PROXY_PASS = os.getenv('PROXY_PASS', '')

        # ============== Scraper Settings ==============
        self.WORKERS = int(os.getenv('WORKERS', '20'))
        self.DELAY = float(os.getenv('DELAY', '0.3'))
        self.RATE_LIMIT_THRESHOLD = int(os.getenv('RATE_LIMIT_THRESHOLD', '10'))
        self.COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', '15'))
        self.CHECKPOINT_INTERVAL = int(os.getenv('CHECKPOINT_INTERVAL', '50'))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '5'))
        self.RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))

        # ============== Email Notifications (SMTP) ==============
        self.SMTP_HOST = os.getenv('SMTP_HOST', '')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USER = os.getenv('SMTP_USER', '')
        self.SMTP_PASS = os.getenv('SMTP_PASS', '')
        self.NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')
        self.ALERT_EMAIL = os.getenv('ALERT_EMAIL', self.NOTIFICATION_EMAIL)
        self.EMAIL_ON_START = os.getenv('EMAIL_ON_START', 'true').lower() == 'true'
        self.EMAIL_ON_COMPLETE = os.getenv('EMAIL_ON_COMPLETE', 'true').lower() == 'true'
        self.EMAIL_ON_ERROR = os.getenv('EMAIL_ON_ERROR', 'true').lower() == 'true'
        self.EMAIL_INTERVAL_HOURS = int(os.getenv('EMAIL_INTERVAL_HOURS', '6'))

        # ============== Dashboard Settings ==============
        self.DASHBOARD_ENABLED = os.getenv('DASHBOARD_ENABLED', 'true').lower() == 'true'
        self.DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '8080'))
        self.DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '127.0.0.1')
        self.DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'changeme')
        self.DASHBOARD_SECRET_KEY = os.getenv('DASHBOARD_SECRET_KEY', os.urandom(24).hex())

        # ============== Health Check Settings ==============
        self.HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))
        self.MAX_CONSECUTIVE_FAILURES = int(os.getenv('MAX_CONSECUTIVE_FAILURES', '3'))
        self.MEMORY_THRESHOLD_MB = int(os.getenv('MEMORY_THRESHOLD_MB', '3000'))
        self.DISK_SPACE_THRESHOLD_GB = int(os.getenv('DISK_SPACE_THRESHOLD_GB', '5'))
        self.STALE_CHECKPOINT_MINUTES = int(os.getenv('STALE_CHECKPOINT_MINUTES', '30'))

        # ============== Watchdog Settings ==============
        self.WATCHDOG_ENABLED = os.getenv('WATCHDOG_ENABLED', 'true').lower() == 'true'
        self.RESTART_DELAY_SECONDS = int(os.getenv('RESTART_DELAY_SECONDS', '30'))
        self.MAX_RESTARTS_PER_HOUR = int(os.getenv('MAX_RESTARTS_PER_HOUR', '5'))
        self.MAX_TOTAL_RESTARTS = int(os.getenv('MAX_TOTAL_RESTARTS', '20'))

        # ============== Data Validation Settings ==============
        self.VALIDATE_DATA = os.getenv('VALIDATE_DATA', 'true').lower() == 'true'
        self.MIN_FIELDS_REQUIRED = int(os.getenv('MIN_FIELDS_REQUIRED', '3'))
        self.MAX_EMPTY_PERCENTAGE = float(os.getenv('MAX_EMPTY_PERCENTAGE', '0.2'))

        # ============== Performance Settings ==============
        self.ADAPTIVE_RATE_LIMIT = os.getenv('ADAPTIVE_RATE_LIMIT', 'true').lower() == 'true'
        self.BANDWIDTH_LIMIT_MBPS = int(os.getenv('BANDWIDTH_LIMIT_MBPS', '0'))
        self.MEMORY_LIMIT_MB = int(os.getenv('MEMORY_LIMIT_MB', '4000'))

        # ============== Scheduling Settings ==============
        self.SCHEDULE_ENABLED = os.getenv('SCHEDULE_ENABLED', 'false').lower() == 'true'
        self.SCHEDULE_START_TIME = os.getenv('SCHEDULE_START_TIME', '22:00')
        self.SCHEDULE_END_TIME = os.getenv('SCHEDULE_END_TIME', '06:00')
        self.PAUSE_ON_WEEKENDS = os.getenv('PAUSE_ON_WEEKENDS', 'false').lower() == 'true'

        # ============== Cost Tracking ==============
        self.PROXY_COST_PER_GB = float(os.getenv('PROXY_COST_PER_GB', '0.0'))
        self.SERVER_COST_PER_HOUR = float(os.getenv('SERVER_COST_PER_HOUR', '0.50'))

        # ============== Paths ==============
        self.OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'full_scrape'))
        self.LOG_DIR = Path(os.getenv('LOG_DIR', self.OUTPUT_DIR / 'logs'))
        self.URL_FILE = Path(os.getenv('URL_FILE', 'all_product_urls_20251215_230531.txt'))

        # ============== Duplicate Detection ==============
        self.ENABLE_DUPLICATE_DETECTION = os.getenv('ENABLE_DUPLICATE_DETECTION', 'true').lower() == 'true'
        self.DUPLICATE_CHECK_METHOD = os.getenv('DUPLICATE_CHECK_METHOD', 'url_hash')

        # ============== Bandwidth Throttling ==============
        self.ENABLE_BANDWIDTH_THROTTLE = os.getenv('ENABLE_BANDWIDTH_THROTTLE', 'false').lower() == 'true'
        self.MAX_BANDWIDTH_MBPS = int(os.getenv('MAX_BANDWIDTH_MBPS', '10'))

        # Create directories if they don't exist
        self.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        self.LOG_DIR.mkdir(exist_ok=True, parents=True)

    def _validate_required(self):
        """Validate that required configuration is present"""
        errors = []

        # Check required proxy settings
        if not self.PROXY_USER:
            errors.append("PROXY_USER is required")
        if not self.PROXY_PASS:
            errors.append("PROXY_PASS is required")

        # Check email settings if notifications enabled
        if self.EMAIL_ON_START or self.EMAIL_ON_COMPLETE or self.EMAIL_ON_ERROR:
            if not self.SMTP_HOST:
                errors.append("SMTP_HOST is required for email notifications")
            if not self.SMTP_USER:
                errors.append("SMTP_USER is required for email notifications")
            if not self.SMTP_PASS:
                errors.append("SMTP_PASS is required for email notifications")
            if not self.NOTIFICATION_EMAIL:
                errors.append("NOTIFICATION_EMAIL is required for email notifications")

        # Check dashboard password
        if self.DASHBOARD_ENABLED and self.DASHBOARD_PASSWORD == 'changeme':
            print("⚠️  WARNING: Dashboard password is set to default 'changeme'. Please change it in .env!")

        # Check URL file exists
        if not self.URL_FILE.exists():
            errors.append(f"URL file not found: {self.URL_FILE}")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

    def get_proxy_url(self) -> str:
        """Get formatted proxy URL"""
        return f"http://{self.PROXY_USER}:{self.PROXY_PASS}@{self.PROXY_HOST}:{self.PROXY_PORT}"

    def get_proxy_dict(self) -> dict:
        """Get proxy dictionary for requests"""
        proxy_url = self.get_proxy_url()
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    def __repr__(self) -> str:
        """String representation (masks sensitive data)"""
        return f"""Config(
    Proxy: {self.PROXY_HOST}:{self.PROXY_PORT}
    Workers: {self.WORKERS}
    Delay: {self.DELAY}s
    Email: {self.SMTP_HOST} -> {self.NOTIFICATION_EMAIL}
    Dashboard: {'Enabled' if self.DASHBOARD_ENABLED else 'Disabled'} on {self.DASHBOARD_HOST}:{self.DASHBOARD_PORT}
    Output: {self.OUTPUT_DIR}
)"""


# Singleton instance
_config = None


def get_config() -> Config:
    """Get or create configuration singleton"""
    global _config
    if _config is None:
        _config = Config()
    return _config


if __name__ == '__main__':
    # Test configuration loading
    try:
        config = Config()
        print("✅ Configuration loaded successfully!")
        print(config)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
