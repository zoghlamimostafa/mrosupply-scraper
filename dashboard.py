#!/usr/bin/env python3
"""
Web Dashboard for MRO Supply Scraper
Flask-based monitoring interface
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Configuration
DASHBOARD_PASSWORD = None
OUTPUT_DIR = None
CONFIG = None


def init_dashboard(config):
    """
    Initialize dashboard with configuration

    Args:
        config: Configuration object
    """
    global DASHBOARD_PASSWORD, OUTPUT_DIR, CONFIG

    CONFIG = config
    OUTPUT_DIR = config.OUTPUT_DIR

    # Hash the password for security
    DASHBOARD_PASSWORD = generate_password_hash(
        config.DASHBOARD_PASSWORD,
        method='pbkdf2:sha256'
    )

    logger.info(f"Dashboard initialized on port {config.DASHBOARD_PORT}")


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')

        if DASHBOARD_PASSWORD and check_password_hash(DASHBOARD_PASSWORD, password):
            session['logged_in'] = True
            session['login_time'] = time.time()
            logger.info("Dashboard login successful")
            return redirect(url_for('index'))
        else:
            logger.warning("Dashboard login failed")
            return render_template('login.html', error="Invalid password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('logged_in', None)
    session.pop('login_time', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/status')
@login_required
def api_status():
    """Get current scraper status"""
    try:
        # Load checkpoint file
        checkpoint_file = OUTPUT_DIR / 'checkpoint_products.json'

        if not checkpoint_file.exists():
            return jsonify({
                'status': 'starting',
                'message': 'Scraper starting up...',
                'completed': 0,
                'total': 0,
                'percent': 0
            })

        # Read checkpoint
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)

        completed = len(checkpoint)

        # Try to get total from config or estimate
        total = getattr(CONFIG, 'TOTAL_URLS', 1500000) if CONFIG else 1500000

        # Calculate metrics
        percent = (completed / total * 100) if total > 0 else 0

        # Check file age
        file_age = time.time() - checkpoint_file.stat().st_mtime
        is_stale = file_age > 600  # 10 minutes

        status = {
            'status': 'stale' if is_stale else 'running',
            'completed': completed,
            'total': total,
            'percent': round(percent, 2),
            'last_update': datetime.fromtimestamp(
                checkpoint_file.stat().st_mtime
            ).isoformat(),
            'file_age_seconds': round(file_age, 0)
        }

        return jsonify(status)

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'completed': 0,
            'total': 0,
            'percent': 0
        }), 500


@app.route('/api/health')
@login_required
def api_health():
    """Get health check results"""
    try:
        health_file = OUTPUT_DIR / 'health_status.json'

        if not health_file.exists():
            return jsonify({'status': 'unknown', 'message': 'No health data available'})

        with open(health_file, 'r') as f:
            health_data = json.load(f)

        return jsonify(health_data)

    except Exception as e:
        logger.error(f"Error getting health: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analytics')
@login_required
def api_analytics():
    """Get analytics data"""
    try:
        analytics_file = OUTPUT_DIR / 'analytics.json'

        if not analytics_file.exists():
            return jsonify({'message': 'No analytics data available'})

        with open(analytics_file, 'r') as f:
            analytics_data = json.load(f)

        return jsonify(analytics_data)

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/costs')
@login_required
def api_costs():
    """Get cost tracking data"""
    try:
        cost_file = OUTPUT_DIR / 'costs.json'

        if not cost_file.exists():
            return jsonify({'message': 'No cost data available'})

        with open(cost_file, 'r') as f:
            cost_data = json.load(f)

        return jsonify(cost_data)

    except Exception as e:
        logger.error(f"Error getting costs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/recent_products')
@login_required
def api_recent_products():
    """Get recent products"""
    try:
        limit = request.args.get('limit', 20, type=int)

        checkpoint_file = OUTPUT_DIR / 'checkpoint_products.json'

        if not checkpoint_file.exists():
            return jsonify({'products': []})

        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)

        # Get most recent products
        recent = list(checkpoint.values())[-limit:]

        return jsonify({'products': recent})

    except Exception as e:
        logger.error(f"Error getting recent products: {e}")
        return jsonify({'products': [], 'error': str(e)}), 500


@app.route('/api/errors')
@login_required
def api_errors():
    """Get recent errors"""
    try:
        limit = request.args.get('limit', 50, type=int)

        failed_file = OUTPUT_DIR / 'failed_urls.json'

        if not failed_file.exists():
            return jsonify({'errors': []})

        with open(failed_file, 'r') as f:
            failed = json.load(f)

        # Get most recent errors
        recent_errors = []
        for url, data in list(failed.items())[-limit:]:
            recent_errors.append({
                'url': url,
                'error': data.get('error', 'Unknown'),
                'attempts': data.get('attempts', 0),
                'last_attempt': data.get('last_attempt', '')
            })

        return jsonify({'errors': recent_errors})

    except Exception as e:
        logger.error(f"Error getting errors: {e}")
        return jsonify({'errors': [], 'error': str(e)}), 500


@app.route('/api/timeline')
@login_required
def api_timeline():
    """Get timeline data for charts"""
    try:
        hours = request.args.get('hours', 24, type=int)

        timeline_file = OUTPUT_DIR / 'timeline.json'

        if not timeline_file.exists():
            return jsonify({'timeline': []})

        with open(timeline_file, 'r') as f:
            timeline_data = json.load(f)

        # Filter by hours
        cutoff_time = time.time() - (hours * 3600)
        filtered = [
            d for d in timeline_data
            if d.get('timestamp', 0) > cutoff_time
        ]

        return jsonify({'timeline': filtered})

    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        return jsonify({'timeline': [], 'error': str(e)}), 500


@app.route('/api/system')
@login_required
def api_system():
    """Get system resources"""
    try:
        import psutil

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)

        # Disk
        disk = psutil.disk_usage(str(OUTPUT_DIR))
        disk_free_gb = disk.free / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        disk_percent = disk.percent

        system_info = {
            'cpu_percent': round(cpu_percent, 1),
            'memory_percent': round(memory_percent, 1),
            'memory_used_gb': round(memory_used_gb, 2),
            'memory_total_gb': round(memory_total_gb, 2),
            'disk_free_gb': round(disk_free_gb, 2),
            'disk_total_gb': round(disk_total_gb, 2),
            'disk_percent': round(disk_percent, 1),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(system_info)

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500


def run_dashboard(config, host='127.0.0.1', port=None, debug=False):
    """
    Run the dashboard server

    Args:
        config: Configuration object
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: from config)
        debug: Enable debug mode
    """
    # Initialize
    init_dashboard(config)

    # Get port
    if port is None:
        port = config.DASHBOARD_PORT

    # Log startup
    logger.info(f"Starting dashboard on {host}:{port}")
    print(f"\n{'=' * 60}")
    print(f"🌐 Dashboard starting on http://{host}:{port}")
    print(f"   Password: {config.DASHBOARD_PASSWORD}")
    print(f"{'=' * 60}\n")

    # Run Flask app
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False  # Don't use reloader in production
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise


if __name__ == '__main__':
    # Test dashboard
    import sys
    sys.path.insert(0, '.')
    from config import Config

    try:
        config = Config()

        print("Starting MRO Supply Scraper Dashboard")
        print("=" * 60)

        # Run dashboard
        run_dashboard(
            config,
            host='127.0.0.1',
            port=config.DASHBOARD_PORT,
            debug=True
        )

    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
