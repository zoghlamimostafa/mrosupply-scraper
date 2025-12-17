#!/usr/bin/env python3
"""
Comprehensive test: GeoNode proxies vs Direct connection
Tests both methods and compares results
"""

import time
from proxy_manager import ProxyManager
from fast_scraper import FastMROSupplyScraper

def test_geonode_proxies():
    """Test with GeoNode proxies"""
    print("="*70)
    print("TEST 1: GeoNode Proxies")
    print("="*70)

    # Initialize
    scraper = FastMROSupplyScraper(
        output_dir="test_with_geonode",
        max_workers=5,
        use_proxies=True
    )

    print("\n[1/4] Fetching proxies from GeoNode API...")
    total = scraper.proxy_manager.fetch_proxies(limit=300)
    print(f"      ✓ Fetched {total} proxies")

    if total > 0:
        # Show top proxies
        print("\n[2/4] Top 10 proxies by uptime:")
        for i, proxy in enumerate(scraper.proxy_manager.proxies[:10], 1):
            print(f"      {i:2d}. {proxy['address']:20s} | "
                  f"{proxy['type']:6s} | "
                  f"Uptime: {proxy.get('uptime', 0):5.1f}% | "
                  f"Country: {proxy.get('country', 'N/A'):2s}")

        avg_uptime = sum(p.get('uptime', 0) for p in scraper.proxy_manager.proxies) / len(scraper.proxy_manager.proxies)
        print(f"\n      Average uptime: {avg_uptime:.1f}%")

        # Validate sample
        print("\n[3/4] Validating proxy sample (testing 15 proxies)...")
        working = scraper.proxy_manager.validate_proxies(max_test=15, timeout=8)
        print(f"      ✓ Working proxies: {working}/15")

    # Get URLs
    print("\n[4/4] Fetching product URLs...")
    urls = scraper.get_product_urls_from_search(max_pages=1)
    urls = urls[:20]
    print(f"      ✓ Got {len(urls)} product URLs")

    # Scrape with proxies
    print("\n" + "="*70)
    print("Scraping 20 products WITH proxies...")
    print("="*70)
    start = time.time()
    products = scraper.scrape_products_concurrent(urls)
    elapsed = time.time() - start

    # Results
    success_rate = len(products) / len(urls) * 100 if urls else 0
    speed = len(products) / elapsed if elapsed > 0 else 0

    print("\n" + "="*70)
    print("RESULTS WITH PROXIES:")
    print("="*70)
    print(f"Products scraped: {len(products)}/{len(urls)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Time: {elapsed:.1f} seconds")
    print(f"Speed: {speed:.2f} products/second")
    print(f"Proxy requests - Success: {scraper.stats['proxy_success']}, Failed: {scraper.stats['proxy_failed']}")

    if len(products) > 0:
        scraper.save_products(products, suffix="_with_geonode")

    return {
        'method': 'GeoNode Proxies',
        'total': len(urls),
        'success': len(products),
        'time': elapsed,
        'speed': speed,
        'success_rate': success_rate,
        'proxy_count': total,
        'working_proxies': working if total > 0 else 0
    }

def test_direct_connection():
    """Test without proxies (direct connection)"""
    print("\n\n")
    print("="*70)
    print("TEST 2: Direct Connection (No Proxies)")
    print("="*70)

    scraper = FastMROSupplyScraper(
        output_dir="test_direct",
        max_workers=5,
        use_proxies=False
    )

    # Get URLs
    print("\n[1/2] Fetching product URLs...")
    urls = scraper.get_product_urls_from_search(max_pages=1)
    urls = urls[:20]
    print(f"      ✓ Got {len(urls)} product URLs")

    # Scrape direct
    print("\n[2/2] Scraping 20 products WITHOUT proxies...")
    print("="*70)
    start = time.time()
    products = scraper.scrape_products_concurrent(urls)
    elapsed = time.time() - start

    # Results
    success_rate = len(products) / len(urls) * 100 if urls else 0
    speed = len(products) / elapsed if elapsed > 0 else 0

    print("\n" + "="*70)
    print("RESULTS WITHOUT PROXIES:")
    print("="*70)
    print(f"Products scraped: {len(products)}/{len(urls)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Time: {elapsed:.1f} seconds")
    print(f"Speed: {speed:.2f} products/second")

    if len(products) > 0:
        scraper.save_products(products, suffix="_direct")

    return {
        'method': 'Direct Connection',
        'total': len(urls),
        'success': len(products),
        'time': elapsed,
        'speed': speed,
        'success_rate': success_rate,
        'proxy_count': 0,
        'working_proxies': 0
    }

def print_comparison(results1, results2):
    """Print side-by-side comparison"""
    print("\n\n")
    print("="*70)
    print("COMPREHENSIVE COMPARISON")
    print("="*70)
    print("")
    print(f"{'Metric':<30} {'With Proxies':>18} {'Direct':>18}")
    print("-"*70)
    print(f"{'Proxies fetched':<30} {results1['proxy_count']:>18,d} {results2['proxy_count']:>18,d}")
    print(f"{'Working proxies':<30} {results1['working_proxies']:>18,d} {results2['working_proxies']:>18,d}")
    print(f"{'Products attempted':<30} {results1['total']:>18,d} {results2['total']:>18,d}")
    print(f"{'Products scraped':<30} {results1['success']:>18,d} {results2['success']:>18,d}")
    print(f"{'Success rate':<30} {results1['success_rate']:>17.1f}% {results2['success_rate']:>17.1f}%")
    print(f"{'Time (seconds)':<30} {results1['time']:>18.1f} {results2['time']:>18.1f}")
    print(f"{'Speed (products/sec)':<30} {results1['speed']:>18.2f} {results2['speed']:>18.2f}")
    print("="*70)

    # Determine winner
    if results2['success'] > results1['success']:
        winner = "Direct Connection"
        reason = "higher success rate"
    elif results2['speed'] > results1['speed']:
        winner = "Direct Connection"
        reason = "faster speed"
    else:
        winner = "Tie"
        reason = "similar performance"

    print(f"\n🏆 WINNER: {winner} ({reason})")
    print("="*70)

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║        COMPREHENSIVE PROXY TEST - GeoNode vs Direct                 ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("")

    # Run tests
    results_proxy = test_geonode_proxies()
    results_direct = test_direct_connection()

    # Compare
    print_comparison(results_proxy, results_direct)

    print("\n📝 CONCLUSION:")
    if results_direct['success_rate'] > 80 and results_proxy['success_rate'] < 20:
        print("   • Free proxies are blocked by mrosupply.com")
        print("   • Direct connection works excellently")
        print("   • Recommendation: Use direct connection (no proxies)")
    elif results_proxy['success_rate'] > results_direct['success_rate']:
        print("   • Proxies are working!")
        print("   • Recommendation: Use proxies for better performance")
    else:
        print("   • Both methods have similar performance")

    print("\n✅ Test complete!\n")

if __name__ == '__main__':
    main()
