#!/bin/bash
# Recommended usage examples for MROSupply scraper

echo "======================================================================="
echo "MROSupply Scraper - Recommended Usage"
echo "======================================================================="
echo ""

echo "1. QUICK TEST (10 products)"
echo "   Fast test to verify everything works"
echo ""
echo "   python3 fast_scraper.py --max-products 10 --workers 5"
echo ""

echo "2. MEDIUM RUN (100 products) - RECOMMENDED"
echo "   Good for most use cases, fast and reliable"
echo ""
echo "   python3 fast_scraper.py --max-products 100 --workers 10 --output-dir results_100"
echo ""

echo "3. LARGE RUN (500 products)"
echo "   For larger datasets, still fast"
echo ""
echo "   python3 fast_scraper.py --max-products 500 --workers 10 --output-dir results_500"
echo ""

echo "4. FULL CATALOG (1000+ products)"
echo "   Scrape entire catalog (takes ~2-3 minutes per 1000 products)"
echo ""
echo "   python3 fast_scraper.py --max-products 5000 --workers 10 --output-dir full_catalog"
echo ""

echo "5. ESTIMATE ONLY"
echo "   See how many products are available without scraping"
echo ""
echo "   python3 fast_scraper.py --estimate"
echo ""

echo "======================================================================="
echo "Expected Performance (WITHOUT PROXIES - RECOMMENDED)"
echo "======================================================================="
echo "Speed: 8-10 products/second"
echo "Success rate: 99-100%"
echo "10 products: ~1-2 seconds"
echo "100 products: ~10-15 seconds"
echo "1000 products: ~2-3 minutes"
echo ""

echo "======================================================================="
echo "DO NOT USE (Proxies - they don't work for this site)"
echo "======================================================================="
echo "# These will fail due to anti-proxy protection:"
echo "# python3 fast_scraper.py --use-proxies --max-products 50"
echo ""

echo "======================================================================="
echo "Want to run now? Execute one of the commands above!"
echo "======================================================================="
