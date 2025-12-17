#!/usr/bin/env python3
"""
Email Notification System for MRO Supply Scraper
Sends alerts via SMTP for important events
"""

import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Notifier:
    """Email notification manager"""

    def __init__(self, config):
        """Initialize notifier with configuration"""
        self.config = config
        self.last_periodic_update = time.time()
        self.email_queue = []
        self.failed_emails = []

    def send_startup_notification(self, details: Dict):
        """Send notification that scraper has started"""
        if not self.config.EMAIL_ON_START:
            return

        subject = "✅ MRO Supply Scraper Started"
        body = f"""
MRO Supply Scraper has started successfully.

Configuration:
- Workers: {details.get('workers', 'N/A')}
- Target URLs: {details.get('total_urls', 'N/A'):,}
- Output Directory: {details.get('output_dir', 'N/A')}
- Started at: {details.get('start_time', 'N/A')}
- Estimated Completion: {details.get('estimated_completion', 'N/A')}

Dashboard: http://{self.config.DASHBOARD_HOST}:{self.config.DASHBOARD_PORT}

Configuration Summary:
- Rate Limit: Pause after {self.config.RATE_LIMIT_THRESHOLD} 429 errors
- Cooldown: {self.config.COOLDOWN_MINUTES} minutes
- Adaptive Rate Limiting: {'Enabled' if self.config.ADAPTIVE_RATE_LIMIT else 'Disabled'}
- Data Validation: {'Enabled' if self.config.VALIDATE_DATA else 'Disabled'}

You will receive progress updates every {self.config.EMAIL_INTERVAL_HOURS} hours.

---
MRO Supply Autonomous Scraper
        """

        self.send_email(subject, body.strip())

    def send_progress_update(self, stats: Dict):
        """Send periodic progress update"""
        hours_since_last = (time.time() - self.last_periodic_update) / 3600

        if hours_since_last < self.config.EMAIL_INTERVAL_HOURS:
            return

        self.last_periodic_update = time.time()

        subject = f"📊 Progress: {stats['completed']:,}/{stats['total']:,} ({stats['percent']:.1f}%)"
        body = f"""
Scraper Progress Update

Progress: {stats['completed']:,} / {stats['total']:,} ({stats['percent']:.1f}%)
Success Rate: {stats.get('success_rate', 0):.1f}%
Failed: {stats.get('failed', 0):,}

Performance:
- Speed: {stats.get('rate', 0):.2f} products/second
- Elapsed: {stats.get('elapsed_hours', 0):.1f} hours
- ETA: {stats.get('eta_hours', 0):.1f} hours remaining

Proxy Statistics:
- Total Requests: {stats.get('total_requests', 0):,}
- Unique IPs: {stats.get('unique_ips', 0):,}
- Success Rate: {stats.get('proxy_success_rate', 0):.1f}%

System Health:
- Memory: {stats.get('memory_mb', 0):.0f} MB
- Disk Free: {stats.get('disk_free_gb', 0):.1f} GB
- Rate Limit Events: {stats.get('rate_limit_count', 0)}

Dashboard: http://{self.config.DASHBOARD_HOST}:{self.config.DASHBOARD_PORT}

---
MRO Supply Autonomous Scraper
        """

        self.send_email(subject, body.strip())

    def send_completion_notification(self, summary: Dict):
        """Send notification when scraping completes"""
        if not self.config.EMAIL_ON_COMPLETE:
            return

        subject = "✅ MRO Supply Scraper Completed Successfully!"
        body = f"""
Scraping completed successfully!

Final Results:
- Total Scraped: {summary.get('success_count', 0):,}
- Failed: {summary.get('failed_count', 0):,}
- Success Rate: {summary.get('success_rate', 0):.1f}%
- Total Time: {summary.get('total_hours', 0):.1f} hours
- Average Speed: {summary.get('avg_rate', 0):.2f} products/second

Output Files:
- Products JSON: {summary.get('json_file', 'N/A')}
- Products CSV: {summary.get('csv_file', 'N/A')}
- Failed URLs: {summary.get('failed_file', 'N/A')}

Proxy Usage:
- Total Requests: {summary.get('total_requests', 0):,}
- Unique IPs Used: {summary.get('unique_ips', 0):,}
- Bandwidth Used: {summary.get('bandwidth_gb', 0):.2f} GB

Cost Estimate:
- Proxy Cost: ${summary.get('proxy_cost', 0):.2f}
- Server Cost: ${summary.get('server_cost', 0):.2f}
- Total Cost: ${summary.get('total_cost', 0):.2f}

Next Steps:
1. Download files from server
2. Retry failed URLs if needed: {summary.get('failed_count', 0):,} URLs
3. Validate data quality
4. Archive and backup data

Thank you for using MRO Supply Autonomous Scraper!

---
MRO Supply Autonomous Scraper
        """

        self.send_email(subject, body.strip())

    def send_alert(self, message: str, details: Optional[Dict] = None):
        """Send warning alert"""
        if not self.config.EMAIL_ON_ERROR:
            return

        subject = f"⚠️ Scraper Alert: {message}"

        details_str = ""
        if details:
            details_str = "\n\nDetails:\n" + "\n".join(
                f"  {k}: {v}" for k, v in details.items()
            )

        body = f"""
Alert: {message}
{details_str}

Time: {datetime.now().isoformat()}

Check Dashboard: http://{self.config.DASHBOARD_HOST}:{self.config.DASHBOARD_PORT}

This is a warning notification. The scraper is still running but requires attention.

---
MRO Supply Autonomous Scraper
        """

        self.send_email(subject, body.strip(), priority="high")

    def send_critical_alert(self, message: str, details: Optional[Dict] = None):
        """Send critical alert"""
        subject = f"🚨 CRITICAL: {message}"

        details_str = ""
        if details:
            details_str = "\n\nDetails:\n" + "\n".join(
                f"  {k}: {v}" for k, v in details.items()
            )

        body = f"""
CRITICAL ALERT: {message}
{details_str}

Time: {datetime.now().isoformat()}

IMMEDIATE ACTION REQUIRED:
- Check server status
- Verify scraper is running
- Check system resources (memory, disk)
- Review recent logs

Dashboard: http://{self.config.DASHBOARD_HOST}:{self.config.DASHBOARD_PORT}

The scraper may have stopped or encountered a serious error.

---
MRO Supply Autonomous Scraper
        """

        # Send to alert email (may be different from notification email)
        self.send_email(
            subject,
            body.strip(),
            to=self.config.ALERT_EMAIL,
            priority="urgent"
        )

    def send_email(self, subject: str, body: str, to: Optional[str] = None, priority: str = "normal"):
        """Send email via SMTP with retry logic"""
        if not self.config.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email")
            return False

        to_email = to or self.config.NOTIFICATION_EMAIL
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                msg = MIMEMultipart()
                msg['From'] = self.config.SMTP_USER
                msg['To'] = to_email
                msg['Subject'] = subject

                # Set priority headers
                if priority == "urgent":
                    msg['Priority'] = '1'
                    msg['X-Priority'] = '1'
                    msg['Importance'] = 'high'
                elif priority == "high":
                    msg['Priority'] = '2'
                    msg['X-Priority'] = '2'
                    msg['Importance'] = 'high'

                msg.attach(MIMEText(body, 'plain'))

                # Connect and send
                with smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    server.login(self.config.SMTP_USER, self.config.SMTP_PASS)
                    server.send_message(msg)

                logger.info(f"Email sent: {subject}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP authentication failed: {e}")
                return False  # Don't retry auth errors

            except smtplib.SMTPException as e:
                logger.error(f"SMTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.failed_emails.append({'subject': subject, 'time': datetime.now()})
                    return False

            except Exception as e:
                logger.error(f"Failed to send email (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.failed_emails.append({'subject': subject, 'time': datetime.now()})
                    return False

        return False

    def test_email_config(self) -> bool:
        """Test email configuration by sending test email"""
        subject = "🧪 MRO Supply Scraper - Email Test"
        body = """
This is a test email from the MRO Supply Scraper.

If you received this email, your SMTP configuration is correct!

Configuration:
- SMTP Host: {}
- SMTP Port: {}
- From: {}
- To: {}

Email notifications are working properly.

---
MRO Supply Autonomous Scraper
        """.format(
            self.config.SMTP_HOST,
            self.config.SMTP_PORT,
            self.config.SMTP_USER,
            self.config.NOTIFICATION_EMAIL
        )

        success = self.send_email(subject, body.strip())

        if success:
            print("✅ Test email sent successfully!")
            print(f"   Check {self.config.NOTIFICATION_EMAIL} for the test message.")
        else:
            print("❌ Failed to send test email")
            print("   Check your SMTP settings in .env file")
            print(f"   SMTP Host: {self.config.SMTP_HOST}")
            print(f"   SMTP Port: {self.config.SMTP_PORT}")
            print(f"   SMTP User: {self.config.SMTP_USER}")

        return success

    def get_failed_email_count(self) -> int:
        """Get count of failed emails"""
        return len(self.failed_emails)


if __name__ == '__main__':
    # Test email configuration
    import sys
    sys.path.insert(0, '.')
    from config import Config

    try:
        config = Config()
        notifier = Notifier(config)

        print("Testing email configuration...")
        print(f"SMTP: {config.SMTP_HOST}:{config.SMTP_PORT}")
        print(f"From: {config.SMTP_USER}")
        print(f"To: {config.NOTIFICATION_EMAIL}")
        print()

        notifier.test_email_config()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
