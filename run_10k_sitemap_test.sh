#!/bin/bash

# Test 10K products using sitemap approach with Webshare proxies
# Usage: ./run_10k_sitemap_test.sh

WEBSHARE_API_KEY="hqy10ekhqb0jackvwe9fyzf4aosmo28wi6s48zji"

echo "=========================================="
echo "SITEMAP TEST: 10,000 PRODUCTS"
echo "=========================================="
echo ""

python3 crawl4ai_scraper.py \
  --webshare-api-key $WEBSHARE_API_KEY \
  --workers 10 \
  --delay 0.5 \
  --sitemap-start 1 \
  --sitemap-end 5 \
  --max-products 10000 \
  --local-sitemaps . \
  --output-dir test_10k_sitemap_data

echo ""
echo "=========================================="
echo "Test complete! Check test_10k_sitemap_data/"
echo "=========================================="
