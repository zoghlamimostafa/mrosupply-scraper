#!/usr/bin/env python3
"""
Test GeoNode proxies with NEW enhanced anti-detection features
Combines: GeoNode API + Rotating Headers + Human-like behavior
"""

from proxy_manager import ProxyManager
from fast_scraper import FastMROSupplyScraper
import time

def main():
    print("="*70)
    print("GeoNode Proxies + Enhanced Anti-Detection Test")
    print("="*70)
    print("\nFeatures enabled:")
    print("  ✓ GeoNode API (quality proxies)")
    print("  ✓ Rotating browser fingerprints")
    print("  ✓ Realistic headers (Sec-Fetch-*, sec-ch-ua)")
    print("  ✓ Session & cookie management")
    print("  ✓ Referer chains")
    print("  ✓ Human-like timing randomization")
    print("  ✓ Conservative rate limiting")
    print()

    # Initialize scraper with proxies
    scraper = FastMROSupplyScraper(
        output_dir="geonode_enhanced_test",
        max_workers=2,
        use_proxies=True,
        delay_between_requests=2.0  # Extra safe with proxies
    )

    print("[1/4] Fetching proxies from GeoNode API...")
    total = scraper.proxy_manager.fetch_proxies(limit=200)
    print(f"      ✓ Fetched {total} proxies")

    if total == 0:
        print("\n❌ No proxies available!")
        return

    # Show proxy stats
    if scraper.proxy_manager.proxies:
        avg_uptime = sum(p.get('uptime', 0) for p in scraper.proxy_manager.proxies) / len(scraper.proxy_manager.proxies)
        print(f"      Average uptime: {avg_uptime:.1f}%")

        print("\n      Top 5 proxies:")
        for i, p in enumerate(scraper.proxy_manager.proxies[:5], 1):
            print(f"        {i}. {p['address']:20s} | {p['type']:6s} | "
                  f"{p.get('uptime', 0):5.1f}% | {p.get('country', 'N/A'):2s}")

    # Validate sample
    print("\n[2/4] Validating proxy sample (10 proxies, 8s timeout)...")
    working = scraper.proxy_manager.validate_proxies(max_test=10, timeout=8)
    print(f"      ✓ Working proxies: {working}/10")

    # Get product URLs
    print("\n[3/4] Fetching product URLs...")
    urls = scraper.get_product_urls_from_search(max_pages=1)
    urls = urls[:30]  # Test with 30 products
    print(f"      ✓ Got {len(urls)} product URLs")

    # Scrape with proxies + enhanced features
    print("\n[4/4] Scraping with GeoNode proxies + anti-detection...")
    print("="*70)
    print(f"Settings: {scraper.max_workers} workers, {scraper.delay_between_requests}s delay")
    print("="*70)

    start = time.time()
    products = scraper.scrape_products_concurrent(urls)
    elapsed = time.time() - start

    # Results
    success_rate = len(products) / len(urls) * 100 if urls else 0
    speed = len(products) / elapsed if elapsed > 0 else 0

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Products attempted:  {len(urls)}")
    print(f"Products scraped:    {len(products)}")
    print(f"Success rate:        {success_rate:.1f}%")
    print(f"Time:                {elapsed:.1f} seconds")
    print(f"Speed:               {speed:.2f} products/second")
    print()
    print(f"Proxy stats:")
    print(f"  Success:  {scraper.stats['proxy_success']}")
    print(f"  Failed:   {scraper.stats['proxy_failed']}")

    if scraper.stats['proxy_success'] + scraper.stats['proxy_failed'] > 0:
        proxy_rate = scraper.stats['proxy_success'] / (scraper.stats['proxy_success'] + scraper.stats['proxy_failed']) * 100
        print(f"  Rate:     {proxy_rate:.1f}%")

    print("="*70)

    # Conclusion
    if success_rate >= 80:
        print("\n✅ SUCCESS! Proxies + anti-detection are working!")
        print("   The combination is effective.")
    elif success_rate >= 50:
        print("\n⚠️  PARTIAL SUCCESS")
        print("   Some proxies work, but not all.")
    else:
        print("\n❌ PROXIES STILL BLOCKED")
        print("   Free proxies remain blocked despite enhancements.")
        print("   Direct connection recommended.")

    if len(products) > 0:
        scraper.save_products(products, suffix="_geonode_enhanced")

    return {
        'success_rate': success_rate,
        'speed': speed,
        'products': len(products)
    }

if __name__ == '__main__':
    main()
