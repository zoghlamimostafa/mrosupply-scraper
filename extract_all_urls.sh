#!/bin/bash

# Extract ALL 1.5M Product URLs from Sitemaps 1-151
# Usage: ./extract_all_urls.sh

echo "=========================================="
echo "EXTRACTING ALL PRODUCT URLS"
echo "=========================================="
echo ""
echo "This will extract all ~1.5M product URLs from sitemaps 1-151"
echo "Estimated time: 2-5 minutes"
echo ""
read -p "Press Enter to start or Ctrl+C to cancel..."
echo ""

python3 get_all_urls.py \
  --sitemap-start 1 \
  --sitemap-end 151 \
  --format both

echo ""
echo "=========================================="
echo "Done! Check the generated files:"
echo "  - all_product_urls_*.txt (text file)"
echo "  - all_product_urls_*.json (JSON file)"
echo "  - url_extraction_summary_*.txt (summary)"
echo "=========================================="
