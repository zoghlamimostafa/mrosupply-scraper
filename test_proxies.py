#!/usr/bin/env python3
"""
Test script: Download proxies, validate them, and run scraper
"""

from proxy_manager import ProxyManager
from fast_scraper import FastMROSupplyScraper

def main():
    print("="*70)
    print("STEP 1: Downloading Proxies")
    print("="*70)

    # Initialize proxy manager
    proxy_manager = ProxyManager(proxy_types=['http', 'socks5'])

    # Fetch proxies
    total = proxy_manager.fetch_proxies()
    print(f"\nDownloaded {total} total proxies")

    if total == 0:
        print("ERROR: No proxies downloaded!")
        return

    print("\n" + "="*70)
    print("STEP 2: Validating Sample of Proxies")
    print("="*70)

    # Validate a sample
    working = proxy_manager.validate_proxies(max_test=30, timeout=10)
    print(f"\nFound {working} working proxies")

    if working == 0:
        print("\nWARNING: No working proxies found in sample.")
        print("Continuing anyway - will use full proxy list without validation")

    print("\n" + "="*70)
    print("STEP 3: Running Scraper with Proxies")
    print("="*70)

    # Create scraper with proxies
    scraper = FastMROSupplyScraper(
        output_dir="test_with_proxies",
        max_workers=5,
        use_proxies=True
    )

    # Assign the proxy manager
    scraper.proxy_manager = proxy_manager

    # Get product URLs
    print("\nFetching product URLs...")
    product_urls = scraper.get_product_urls_from_search(max_pages=1)

    # Limit to 20 products for testing
    product_urls = product_urls[:20]
    print(f"\nScraping {len(product_urls)} products with proxies...")

    # Scrape
    products = scraper.scrape_products_concurrent(product_urls)

    # Save
    scraper.save_products(products, suffix="_with_proxies")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print(f"Successfully scraped: {len(products)} products")
    print("\nProxy Statistics:")
    proxy_manager.print_stats()

if __name__ == '__main__':
    main()
