#!/usr/bin/env python3
"""
Test your 8 proxies with real scraping to measure:
1. Success rate
2. Requests per proxy before ban
3. Total capacity
4. Time estimate for 1.5M products
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime

# Your 8 working proxies
PROXIES_LIST = [
    "142.111.48.253:7030:yopfgyku:pn4xri0h48sy",
    "31.59.20.176:6754:yopfgyku:pn4xri0h48sy",
    "23.95.150.145:6114:yopfgyku:pn4xri0h48sy",
    "198.105.121.200:6462:yopfgyku:pn4xri0h48sy",
    "64.137.96.74:6641:yopfgyku:pn4xri0h48sy",
    "84.247.60.125:6095:yopfgyku:pn4xri0h48sy",
    "216.10.27.159:6837:yopfgyku:pn4xri0h48sy",
    "142.111.67.146:5611:yopfgyku:pn4xri0h48sy"
]

def parse_proxy(proxy_str):
    """Convert IP:PORT:USER:PASS to proxy dict"""
    parts = proxy_str.split(':')
    ip, port, username, password = parts[0], parts[1], parts[2], parts[3]
    proxy_url = f"http://{username}:{password}@{ip}:{port}"
    return {
        'http': proxy_url,
        'https': proxy_url,
        'address': f"{ip}:{port}",
        'ip': ip
    }

def get_product_urls(session, proxies, max_products=100):
    """Get product URLs from search"""
    print(f"Fetching product URLs...")
    search_url = "https://www.mrosupply.com/search"
    product_urls = []

    for page in range(1, 11):  # Try up to 10 pages
        try:
            params = {'page': page}
            response = session.get(search_url, params=params, proxies=proxies, timeout=15)

            if response.status_code != 200:
                print(f"  Page {page}: Status {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find product links
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                # Match product URLs (various patterns)
                if any(x in href for x in ['/hydraulics-', '/electrical-', '/mechanical-', '/tools-']):
                    if href.startswith('/'):
                        href = 'https://www.mrosupply.com' + href
                    if href not in product_urls:
                        product_urls.append(href)
                        if len(product_urls) >= max_products:
                            break

            print(f"  Page {page}: Found {len(product_urls)} products")

            if len(product_urls) >= max_products:
                break

            time.sleep(1)

        except Exception as e:
            print(f"  Page {page}: Error - {str(e)[:50]}")
            break

    return product_urls[:max_products]

def scrape_product(session, url, proxies):
    """Scrape a single product"""
    try:
        response = session.get(url, proxies=proxies, timeout=15)

        if response.status_code != 200:
            return {'success': False, 'status': response.status_code}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract basic info
        name = soup.find('h1')
        name = name.get_text(strip=True) if name else None

        price = soup.find('span', class_='price')
        if not price:
            price = soup.find('div', {'class': 'price'})
        price = price.get_text(strip=True) if price else None

        return {
            'success': True,
            'status': 200,
            'has_data': bool(name),
            'url': url
        }

    except Exception as e:
        return {'success': False, 'status': 'error', 'error': str(e)[:50]}

def main():
    print("="*70)
    print("TESTING YOUR 8 PROXIES WITH REAL SCRAPING")
    print("="*70)
    print(f"Test parameters:")
    print(f"  - Proxies: {len(PROXIES_LIST)}")
    print(f"  - Target: 200 products (25 per proxy)")
    print(f"  - Strategy: Round-robin rotation")
    print(f"  - Delay: 1.5 seconds between requests")
    print("="*70)
    print()

    # Parse proxies
    proxies_data = [parse_proxy(p) for p in PROXIES_LIST]

    # Stats
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'by_proxy': defaultdict(lambda: {'success': 0, 'failed': 0, 'errors': []})
    }

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    # Get product URLs using first proxy
    print("Step 1: Getting product URLs...")
    first_proxy = proxies_data[0]
    product_urls = get_product_urls(session, first_proxy, max_products=200)

    if not product_urls:
        print("\n❌ Failed to get product URLs!")
        print("   Your proxies might be blocked or search page structure changed.")
        return

    print(f"\n✅ Got {len(product_urls)} product URLs\n")

    # Test scraping with rotation
    print("Step 2: Testing scraping with proxy rotation...")
    print(f"{'#':<4} {'Proxy':<20} {'Status':<15} {'Success Rate':<15}")
    print("-"*70)

    start_time = time.time()

    for i, url in enumerate(product_urls):
        # Round-robin proxy selection
        proxy = proxies_data[i % len(proxies_data)]
        proxy_ip = proxy['ip']

        # Scrape product
        result = scrape_product(session, url, proxy)

        stats['total'] += 1

        if result['success']:
            stats['success'] += 1
            stats['by_proxy'][proxy_ip]['success'] += 1
            status = f"✅ {result['status']}"
        else:
            stats['failed'] += 1
            stats['by_proxy'][proxy_ip]['failed'] += 1
            stats['by_proxy'][proxy_ip]['errors'].append(result.get('status', 'unknown'))
            status = f"❌ {result.get('status', 'error')}"

        success_rate = (stats['success'] / stats['total']) * 100

        print(f"{i+1:<4} {proxy['address']:<20} {status:<15} {success_rate:>5.1f}%")

        # Progress updates
        if (i + 1) % 25 == 0:
            elapsed = time.time() - start_time
            speed = (i + 1) / elapsed
            remaining = (len(product_urls) - i - 1) / speed if speed > 0 else 0
            print(f"\n--- Progress: {i+1}/{len(product_urls)} | Speed: {speed:.2f}/s | ETA: {remaining/60:.1f}m ---\n")

        time.sleep(1.5)  # Delay between requests

    end_time = time.time()
    total_time = end_time - start_time

    # Final results
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Total requests:      {stats['total']}")
    print(f"Successful:          {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"Failed:              {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
    print(f"Total time:          {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Avg per request:     {total_time/stats['total']:.2f} seconds")
    print(f"Effective speed:     {stats['total']/total_time:.2f} requests/second")

    print("\n" + "="*70)
    print("PER-PROXY BREAKDOWN")
    print("="*70)
    print(f"{'Proxy':<20} {'Requests':<10} {'Success':<10} {'Failed':<10} {'Rate':<10}")
    print("-"*70)

    for proxy in proxies_data:
        proxy_ip = proxy['ip']
        pstats = stats['by_proxy'][proxy_ip]
        total = pstats['success'] + pstats['failed']
        rate = (pstats['success'] / total * 100) if total > 0 else 0
        print(f"{proxy_ip:<20} {total:<10} {pstats['success']:<10} {pstats['failed']:<10} {rate:<9.0f}%")

    # Calculate estimates
    success_rate = stats['success'] / stats['total']
    effective_speed = (stats['total'] / total_time) * success_rate

    print("\n" + "="*70)
    print("ESTIMATES FOR 1,508,692 PRODUCTS")
    print("="*70)
    print(f"Success rate:        {success_rate*100:.1f}%")
    print(f"Effective speed:     {effective_speed:.2f} products/second")
    print(f"Products per hour:   {effective_speed * 3600:.0f}")
    print(f"Products per day:    {effective_speed * 3600 * 24:.0f}")

    hours_needed = 1508692 / (effective_speed * 3600)
    days_needed = hours_needed / 24

    print(f"\nEstimated time:      {hours_needed:.1f} hours ({days_needed:.1f} days)")

    # Cost calculation (if proxies were paid)
    print("\n" + "="*70)
    print("COST ANALYSIS (Assuming proxies already paid)")
    print("="*70)
    print(f"Server cost (VPS):   $10-40/month")
    print(f"Bandwidth:           ~200 GB ($0-10)")
    print(f"Total cost:          $10-50")
    print(f"Per product:         ${10/1508692:.8f} - ${50/1508692:.8f}")

    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)

    if success_rate >= 0.90 and days_needed <= 5:
        print("✅ EXCELLENT: High success rate, fast speed")
        print("   Your proxies are working great!")
        print(f"   Can complete 1.5M products in {days_needed:.1f} days")
        print("   RECOMMENDED: Proceed with production scraping")
    elif success_rate >= 0.80 and days_needed <= 7:
        print("✅ GOOD: Decent success rate, acceptable speed")
        print(f"   Can complete 1.5M products in {days_needed:.1f} days")
        print("   RECOMMENDED: Usable for production with retry logic")
    elif success_rate >= 0.70 and days_needed <= 14:
        print("⚠️ MODERATE: Acceptable but not ideal")
        print(f"   Will take {days_needed:.1f} days for 1.5M products")
        print("   Consider: Improve settings or use better proxies")
    elif success_rate >= 0.50:
        print("⚠️ POOR: Low success rate")
        print(f"   Will take {days_needed:.1f} days with many failures")
        print("   NOT RECOMMENDED: Consider alternative approaches")
    else:
        print("❌ FAILED: Too many failures")
        print("   Proxies are not suitable for this site")
        print("   RECOMMENDED: Use free direct connection instead")

    print("="*70)

    # Save results
    results = {
        'test_date': datetime.now().isoformat(),
        'proxies_tested': len(proxies_data),
        'products_tested': stats['total'],
        'success_rate': success_rate,
        'total_time_seconds': total_time,
        'effective_speed': effective_speed,
        'estimated_days_for_1_5m': days_needed,
        'per_proxy_stats': dict(stats['by_proxy'])
    }

    with open('proxy_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: proxy_test_results.json")

if __name__ == '__main__':
    main()
