#!/bin/bash
# Automated VPS Setup Script for MROSupply Scraper
# Run this on your VPS after uploading files

set -e  # Exit on error

echo "=========================================="
echo "VPS Setup for MROSupply Scraper"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "Please don't run as root. Run as regular user."
   exit 1
fi

# 1. Update system
echo "Step 1/6: Updating system..."
sudo apt update -y
sudo apt upgrade -y

# 2. Install dependencies
echo ""
echo "Step 2/6: Installing Python and tools..."
sudo apt install -y python3 python3-pip screen htop

# 3. Install Python packages
echo ""
echo "Step 3/6: Installing Python packages..."
pip3 install --user beautifulsoup4 requests lxml

# 4. Verify installation
echo ""
echo "Step 4/6: Verifying installation..."
python3 --version
pip3 list | grep beautifulsoup4 || echo "Warning: beautifulsoup4 not found"
pip3 list | grep requests || echo "Warning: requests not found"

# 5. Test scraper
echo ""
echo "Step 5/6: Testing scraper with example file..."
if [ -f "scraper.py" ]; then
    python3 scraper.py --mode test 2>&1 | head -20
    echo "Test completed!"
else
    echo "Warning: scraper.py not found in current directory"
fi

# 6. Run calculator
echo ""
echo "Step 6/6: Running performance calculator..."
if [ -f "vps_calculator.py" ]; then
    python3 vps_calculator.py 1508692 16 4
else
    echo "Warning: vps_calculator.py not found"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the performance estimates above"
echo "2. Start scraping with:"
echo "   screen -S scraper"
echo "   python3 batch_scraper.py --workers 16 --batch-size 241920"
echo ""
echo "3. Detach from screen: Ctrl+A, then D"
echo "4. Reattach later: screen -r scraper"
echo ""
echo "IMPORTANT: Change your server password after this!"
echo "Run: passwd"
echo ""
