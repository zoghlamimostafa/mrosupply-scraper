#!/bin/bash
# START FULL 1.5M PRODUCT SCRAPE
# Run this script to begin scraping all products

echo "========================================================================"
echo "STARTING 1.5M PRODUCT SCRAPE WITH ROTATING RESIDENTIAL PROXY"
echo "========================================================================"
echo ""
echo "Configuration:"
echo "  - Products: 1,508,714"
echo "  - Proxy: Rotating Residential (6.6M US IPs)"
echo "  - Workers: 10"
echo "  - Delay: 0.3s"
echo "  - Timeout: 45s"
echo "  - Retries: 3"
echo ""
echo "Estimates:"
echo "  - Time: ~29 days"
echo "  - Success rate: ~75%"
echo "  - Expected failures: ~375,000 (will retry later)"
echo "  - Bandwidth: ~226 GB"
echo "  - Cost: $2,260 - $3,390"
echo ""
echo "Output:"
echo "  - Directory: full_scrape_1.5m"
echo "  - Checkpoint every 50 products"
echo "  - Final files: products_*.json and products_*.csv"
echo ""
echo "========================================================================"
echo ""

read -p "Ready to start? This will run for ~29 days. Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "🚀 Starting scraper..."
echo ""

# Run the scraper
python3 scraper_rotating_residential.py \
  --workers 10 \
  --delay 0.3 \
  --output-dir full_scrape_1.5m

echo ""
echo "========================================================================"
echo "✅ Scraping complete!"
echo "========================================================================"
echo ""
echo "Check results:"
echo "  ls -lh full_scrape_1.5m/"
echo ""
echo "If there are failed URLs, retry them with:"
echo "  python3 retry_failed.py full_scrape_1.5m/failed_urls_*.txt retry_pass2"
echo ""
