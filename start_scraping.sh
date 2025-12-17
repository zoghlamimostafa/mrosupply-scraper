#!/bin/bash
# Start scraping in background with screen

echo "=========================================="
echo "Starting MROSupply Scraper"
echo "=========================================="
echo ""

# Check if scraper files exist
if [ ! -f "batch_scraper.py" ]; then
    echo "Error: batch_scraper.py not found!"
    echo "Make sure you're in the correct directory."
    exit 1
fi

# Check if already running
if screen -list | grep -q "scraper"; then
    echo "Scraper is already running!"
    echo "To view it: screen -r scraper"
    echo "To kill it: screen -X -S scraper quit"
    exit 1
fi

# Ask for confirmation
echo "This will start scraping ~1.5M products"
echo "Estimated time: 37 hours (1.6 days)"
echo "Workers: 16"
echo "Batch size: 241,920 products per batch"
echo ""
read -p "Start scraping? [y/N]: " confirm

if [[ $confirm != [yY] ]]; then
    echo "Cancelled."
    exit 0
fi

# Create screen session and start scraper
echo ""
echo "Starting scraper in screen session..."
echo "To view progress: screen -r scraper"
echo "To detach: Ctrl+A, then D"
echo ""

screen -dmS scraper bash -c "python3 batch_scraper.py --workers 16 --batch-size 241920; echo 'Scraping complete! Press any key to exit.'; read"

sleep 2

if screen -list | grep -q "scraper"; then
    echo "✓ Scraper started successfully!"
    echo ""
    echo "Commands:"
    echo "  View live progress: screen -r scraper"
    echo "  Check files: ls -lh scraped_data/"
    echo "  Check state: cat scraped_data/batch_state.json"
    echo ""
else
    echo "✗ Failed to start scraper"
    exit 1
fi
