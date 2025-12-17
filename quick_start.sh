#!/bin/bash

# Quick Start Script for MROSupply Scraper
# Makes it easy to run common scraping scenarios

echo "=========================================="
echo "MROSupply.com Fast Scraper - Quick Start"
echo "=========================================="
echo ""
echo "Choose an option:"
echo ""
echo "1. Estimate total products (no scraping)"
echo "2. Test scrape 50 products"
echo "3. Scrape 500 products (fast test)"
echo "4. Scrape ALL products (recommended: 10 workers)"
echo "5. Scrape ALL products (aggressive: 20 workers)"
echo "6. Custom scrape"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "Running estimation..."
        python3 fast_scraper.py --estimate
        ;;
    2)
        echo ""
        echo "Test scraping 50 products..."
        python3 fast_scraper.py --max-products 50 --workers 10 --output-dir test_50
        ;;
    3)
        echo ""
        echo "Scraping 500 products..."
        python3 fast_scraper.py --max-products 500 --workers 10 --output-dir products_500
        ;;
    4)
        echo ""
        echo "Scraping ALL products with 10 workers..."
        echo "Estimated time: 2-3 minutes"
        python3 fast_scraper.py --workers 10
        ;;
    5)
        echo ""
        echo "Scraping ALL products with 20 workers (aggressive)..."
        echo "Estimated time: 1-2 minutes"
        echo "Warning: Higher risk of rate limiting"
        read -p "Continue? [y/N]: " confirm
        if [[ $confirm == [yY] ]]; then
            python3 fast_scraper.py --workers 20
        else
            echo "Cancelled."
        fi
        ;;
    6)
        echo ""
        read -p "Number of workers [10]: " workers
        workers=${workers:-10}
        read -p "Max products (leave empty for all): " max_products
        read -p "Output directory [scraped_data]: " output_dir
        output_dir=${output_dir:-scraped_data}

        cmd="python3 fast_scraper.py --workers $workers --output-dir $output_dir"
        if [ ! -z "$max_products" ]; then
            cmd="$cmd --max-products $max_products"
        fi

        echo ""
        echo "Running: $cmd"
        $cmd
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done!"
