#!/usr/bin/env python3
"""
Test GeoNode proxies with the scraper
"""

from proxy_manager import ProxyManager
from fast_scraper import FastMROSupplyScraper

def main():
    print("="*70)
    print("Testing GeoNode Proxies")
    print("="*70)

    # Initialize proxy manager with GeoNode
    proxy_manager = ProxyManager(proxy_types=['http', 'socks5'], use_geonode=True)

    # Fetch proxies
    total = proxy_manager.fetch_proxies(limit=200)
    print(f"\nFetched {total} proxies from GeoNode")

    if total == 0:
        print("ERROR: No proxies fetched!")
        return

    # Show top 5 proxies by uptime
    print("\nTop 5 proxies by uptime:")
    for i, proxy in enumerate(proxy_manager.proxies[:5], 1):
        print(f"  {i}. {proxy['address']} - {proxy['type']} - "
              f"Uptime: {proxy.get('uptime', 0):.1f}% - "
              f"Country: {proxy.get('country', 'N/A')}")

    # Validate proxies
    print("\n" + "="*70)
    print("Validating Proxies")
    print("="*70)
    working = proxy_manager.validate_proxies(max_test=20, timeout=8)
    print(f"\nWorking proxies: {working}")

    if working == 0:
        print("\nWARNING: No working proxies found. Will try scraping anyway...")

    # Test scraping with proxies
    print("\n" + "="*70)
    print("Testing Scraper with Proxies")
    print("="*70)

    scraper = FastMROSupplyScraper(
        output_dir="test_geonode",
        max_workers=5,
        use_proxies=True
    )
    scraper.proxy_manager = proxy_manager

    # Get product URLs
    product_urls = scraper.get_product_urls_from_search(max_pages=1)
    product_urls = product_urls[:10]

    print(f"\nScraping {len(product_urls)} products with GeoNode proxies...")

    # Scrape
    products = scraper.scrape_products_concurrent(product_urls)

    # Results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Successfully scraped: {len(products)}/{len(product_urls)} products")
    print(f"Success rate: {len(products)/len(product_urls)*100:.1f}%")

    if len(products) > 0:
        scraper.save_products(products, suffix="_geonode")
        print("\n✓ Proxies are working!")
    else:
        print("\n✗ Proxies still not working reliably")

    proxy_manager.print_stats()

if __name__ == '__main__':
    main()
