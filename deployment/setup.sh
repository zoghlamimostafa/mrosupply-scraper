#!/usr/bin/env bash
#
# MRO Supply Scraper - Installation Script
# Automated setup for Ubuntu/Debian servers
#
# Usage: sudo bash deployment/setup.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/mrosupply-scraper"
SCRAPER_USER="scraper"
SCRAPER_GROUP="scraper"
PYTHON_VERSION="3.9"

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Main installation steps
main() {
    log_info "Starting MRO Supply Scraper installation..."
    echo ""

    check_root

    # Step 1: Check OS
    log_info "Step 1/10: Checking operating system..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
            log_warn "This script is designed for Ubuntu/Debian. Your OS: $ID"
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    # Step 2: Update system
    log_info "Step 2/10: Updating system packages..."
    apt-get update -qq
    apt-get upgrade -y -qq

    # Step 3: Install dependencies
    log_info "Step 3/10: Installing system dependencies..."
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        git \
        curl \
        wget \
        rsync \
        logrotate \
        cron

    # Step 4: Create user and group
    log_info "Step 4/10: Creating scraper user and group..."
    if ! getent group "$SCRAPER_GROUP" > /dev/null 2>&1; then
        groupadd "$SCRAPER_GROUP"
        log_info "Created group: $SCRAPER_GROUP"
    else
        log_info "Group $SCRAPER_GROUP already exists"
    fi

    if ! id "$SCRAPER_USER" > /dev/null 2>&1; then
        useradd -r -g "$SCRAPER_GROUP" -d "$INSTALL_DIR" -s /bin/bash -c "MRO Supply Scraper" "$SCRAPER_USER"
        log_info "Created user: $SCRAPER_USER"
    else
        log_info "User $SCRAPER_USER already exists"
    fi

    # Step 5: Create directory structure
    log_info "Step 5/10: Creating directory structure..."
    mkdir -p "$INSTALL_DIR"/{logs,data,backups,reports,utils,templates,deployment}

    # Step 6: Copy application files
    log_info "Step 6/10: Copying application files..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    # Copy Python files
    rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
        "$SCRIPT_DIR"/*.py "$INSTALL_DIR/" 2>/dev/null || true

    # Copy utils
    rsync -av --exclude='__pycache__' --exclude='*.pyc' \
        "$SCRIPT_DIR"/utils/ "$INSTALL_DIR/utils/" 2>/dev/null || true

    # Copy templates
    rsync -av "$SCRIPT_DIR"/templates/ "$INSTALL_DIR/templates/" 2>/dev/null || true

    # Copy deployment files
    rsync -av "$SCRIPT_DIR"/deployment/ "$INSTALL_DIR/deployment/" 2>/dev/null || true

    # Copy .env.example if exists
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env.example"
    fi

    # Copy requirements.txt
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"
    fi

    # Copy URL list if exists
    if [ -f "$SCRIPT_DIR/product_urls.txt" ]; then
        cp "$SCRIPT_DIR/product_urls.txt" "$INSTALL_DIR/data/product_urls.txt"
    fi

    # Step 7: Create Python virtual environment
    log_info "Step 7/10: Creating Python virtual environment..."
    cd "$INSTALL_DIR"

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi

    # Step 8: Install Python packages
    log_info "Step 8/10: Installing Python packages..."
    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
        pip3 install --upgrade pip -q
        pip3 install -r requirements.txt -q
        log_info "Python packages installed"
    else
        log_warn "requirements.txt not found"
    fi

    # Step 9: Set permissions
    log_info "Step 9/10: Setting permissions..."
    chown -R "$SCRAPER_USER:$SCRAPER_GROUP" "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    chmod 700 "$INSTALL_DIR"/.env 2>/dev/null || true

    # Make scripts executable
    chmod +x "$INSTALL_DIR"/*.py 2>/dev/null || true
    chmod +x "$INSTALL_DIR"/deployment/*.sh 2>/dev/null || true

    # Step 10: Install systemd service
    log_info "Step 10/10: Installing systemd service..."

    if [ -f "$INSTALL_DIR/deployment/mrosupply-scraper.service" ]; then
        cp "$INSTALL_DIR/deployment/mrosupply-scraper.service" /etc/systemd/system/
        systemctl daemon-reload
        log_info "Systemd service installed"
    else
        log_warn "Service file not found"
    fi

    # Install logrotate configuration
    if [ -f "$INSTALL_DIR/deployment/logrotate.conf" ]; then
        cp "$INSTALL_DIR/deployment/logrotate.conf" /etc/logrotate.d/mrosupply-scraper
        log_info "Logrotate configuration installed"
    fi

    # Print completion message
    echo ""
    echo "======================================================================"
    log_info "Installation completed successfully!"
    echo "======================================================================"
    echo ""
    log_info "Next steps:"
    echo ""
    echo "  1. Configure environment:"
    echo "     sudo nano $INSTALL_DIR/.env"
    echo ""
    echo "  2. Set your proxy credentials, SMTP settings, etc."
    echo ""
    echo "  3. Test email configuration (optional):"
    echo "     sudo -u scraper $INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/notifier.py"
    echo ""
    echo "  4. Install cron jobs (optional):"
    echo "     sudo crontab -u scraper -e"
    echo "     # Then paste contents from: $INSTALL_DIR/deployment/cron_jobs"
    echo ""
    echo "  5. Enable and start the service:"
    echo "     sudo systemctl enable mrosupply-scraper"
    echo "     sudo systemctl start mrosupply-scraper"
    echo ""
    echo "  6. Check service status:"
    echo "     sudo systemctl status mrosupply-scraper"
    echo ""
    echo "  7. View logs:"
    echo "     sudo journalctl -u mrosupply-scraper -f"
    echo ""
    echo "  8. Access dashboard:"
    echo "     ssh -L 8080:localhost:8080 user@server"
    echo "     Then open: http://localhost:8080"
    echo ""
    echo "======================================================================"
    echo ""
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Service user: $SCRAPER_USER"
    log_info "Service name: mrosupply-scraper"
    echo ""
}

# Run main installation
main

exit 0
