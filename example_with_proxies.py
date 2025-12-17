#!/usr/bin/env python3
"""
Example usage of the MROSupply scraper with proxy rotation
"""

from fast_scraper import FastMROSupplyScraper

def example_with_proxies():
    """Example: Scraping with proxy rotation enabled"""
    print("Example 1: Scraping 10 products with proxy rotation\n")

    # Create scraper with proxy support
    scraper = FastMROSupplyScraper(
        output_dir="scraped_with_proxies",
        max_workers=5,
        use_proxies=True
    )

    # Fetch and validate proxies
    print("Setting up proxies...")
    scraper.proxy_manager.fetch_proxies()
    scraper.proxy_manager.validate_proxies(max_test=30)

    # Get product URLs
    product_urls = scraper.get_product_urls_from_search(max_pages=1)
    product_urls = product_urls[:10]  # Limit to 10 products

    # Scrape with proxies
    products = scraper.scrape_products_concurrent(product_urls)

    # Save results
    scraper.save_products(products, suffix="_with_proxies")

    print("\nProxy statistics:")
    scraper.proxy_manager.print_stats()


def example_without_proxies():
    """Example: Regular scraping without proxies"""
    print("\nExample 2: Scraping 10 products without proxies\n")

    scraper = FastMROSupplyScraper(
        output_dir="scraped_no_proxies",
        max_workers=5,
        use_proxies=False
    )

    product_urls = scraper.get_product_urls_from_search(max_pages=1)
    product_urls = product_urls[:10]

    products = scraper.scrape_products_concurrent(product_urls)
    scraper.save_products(products, suffix="_no_proxies")


if __name__ == '__main__':
    # Run with proxies
    example_with_proxies()

    # Uncomment to compare with non-proxy version
    # example_without_proxies()
