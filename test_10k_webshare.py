https://demo.el-makina.tn/shop/#!/usr/bin/env python3
"""
Test Scraper - 10,000 products with 10 Webshare Proxies
Quick test to validate proxy performance
"""

import json
import csv
import time
import random
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class WebshareProxyManager:
    """Manage 10 Webshare proxies"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.proxies = []
        self.proxy_index = 0
        self.proxy_lock = Lock()
        self.proxy_stats = {}

    def fetch_proxies(self, limit: int = 10):
        """Fetch proxies from Webshare API"""
        print(f"Fetching {limit} proxies from Webshare API...")

        url = f"https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size={limit}"
        headers = {
            "Authorization": f"Token {self.api_key}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse proxy data
            for proxy_data in data.get('results', []):
                proxy_address = proxy_data.get('proxy_address')
                port = proxy_data.get('port')
                username = proxy_data.get('username')
                password = proxy_data.get('password')

                if proxy_address and port:
                    proxy_url = f"http://{username}:{password}@{proxy_address}:{port}"
                    proxy_obj = {
                        'http': proxy_url,
                        'https': proxy_url,
                        'address': f"{proxy_address}:{port}",
                        'id': f"{proxy_address}:{port}"
                    }
                    self.proxies.append(proxy_obj)
                    self.proxy_stats[proxy_obj['id']] = {'success': 0, 'failed': 0}

            print(f"✅ Fetched {len(self.proxies)} proxies from Webshare")

            # Display proxies
            print(f"\nProxies loaded:")
            for i, proxy in enumerate(self.proxies, 1):
                print(f"  {i}. {proxy['address']}")
            print()

            return len(self.proxies) > 0

        except Exception as e:
            print(f"❌ Failed to fetch proxies: {e}")
            return False

    def test_proxy(self, proxy: dict) -> bool:
        """Test a single proxy"""
        try:
            response = requests.get(
                "https://www.mrosupply.com",
                proxies=proxy,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except:
            return False

    def validate_all_proxies(self):
        """Validate all proxies"""
        print(f"{'='*70}")
        print(f"TESTING PROXIES")
        print(f"{'='*70}")

        working = []
        failed = []

        for i, proxy in enumerate(self.proxies, 1):
            print(f"Testing proxy {i}/{len(self.proxies)}: {proxy['address']}...", end=' ')

            success_count = 0
            for _ in range(3):  # Test 3 times
                if self.test_proxy(proxy):
                    success_count += 1
                time.sleep(0.3)

            if success_count >= 2:  # At least 2/3 success
                working.append(proxy)
                print(f"✅ Working ({success_count}/3)")
            else:
                failed.append(proxy)
                print(f"❌ Failed ({success_count}/3)")

        self.proxies = working

        print(f"\n{'='*70}")
        print(f"Validation Results:")
        print(f"  Working: {len(working)}")
        print(f"  Failed: {len(failed)}")
        print(f"{'='*70}\n")

        return len(working) > 0

    def get_next_proxy(self):
        """Get next proxy in rotation"""
        if not self.proxies:
            return None

        with self.proxy_lock:
            proxy = self.proxies[self.proxy_index % len(self.proxies)]
            self.proxy_index += 1
            return proxy

    def mark_success(self, proxy: dict):
        """Mark proxy success"""
        if proxy and proxy['id'] in self.proxy_stats:
            self.proxy_stats[proxy['id']]['success'] += 1

    def mark_failed(self, proxy: dict):
        """Mark proxy failure"""
        if proxy and proxy['id'] in self.proxy_stats:
            self.proxy_stats[proxy['id']]['failed'] += 1

    def print_stats(self):
        """Print proxy statistics"""
        print(f"\n{'='*70}")
        print(f"PROXY STATISTICS")
        print(f"{'='*70}")

        total_success = 0
        total_failed = 0

        for proxy_id, stats in self.proxy_stats.items():
            success = stats['success']
            failed = stats['failed']
            total = success + failed
            success_rate = (success / total * 100) if total > 0 else 0

            total_success += success
            total_failed += failed

            print(f"  {proxy_id}")
            print(f"    Success: {success} | Failed: {failed} | Rate: {success_rate:.1f}%")

        overall_total = total_success + total_failed
        overall_rate = (total_success / overall_total * 100) if overall_total > 0 else 0

        print(f"\n  Overall:")
        print(f"    Total requests: {overall_total}")
        print(f"    Success: {total_success} ({overall_rate:.1f}%)")
        print(f"    Failed: {total_failed} ({100-overall_rate:.1f}%)")
        print(f"{'='*70}\n")


class TestScraper:
    """Test scraper for 10k products"""

    def __init__(self, output_dir: str = "test_10k_data", workers: int = 10, delay: float = 0.5):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.delay = delay
        self.products_lock = Lock()
        self.stats_lock = Lock()

        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None,
        }

        self.proxy_manager = None

        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch page with proxy"""
        for attempt in range(max_retries):
            proxy = None
            try:
                if self.proxy_manager:
                    proxy = self.proxy_manager.get_next_proxy()

                if proxy:
                    response = self.session.get(url, proxies=proxy, timeout=15)
                else:
                    response = self.session.get(url, timeout=15)

                response.raise_for_status()

                if proxy:
                    self.proxy_manager.mark_success(proxy)

                return BeautifulSoup(response.text, 'html.parser')

            except Exception as e:
                if proxy:
                    self.proxy_manager.mark_failed(proxy)

                if attempt < max_retries - 1:
                    time.sleep(0.5)

        return None

    def extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product data"""
        product = {
            'url': url,
            'name': '',
            'brand': '',
            'mpn': '',
            'sku': '',
            'price': '',
            'category': '',
        }

        # Extract from JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if data.get('@type') == 'Product':
                    product['name'] = data.get('name', '')
                    product['category'] = data.get('category', '')

                    offers = data.get('offers', [])
                    if isinstance(offers, list) and offers:
                        offer = offers[0]
                        product['sku'] = str(offer.get('sku', ''))
                        product['mpn'] = offer.get('mpn', '')
                        product['price'] = f"${offer.get('price', '')}"
            except:
                pass

        # Brand
        brand_meta = soup.find('meta', {'name': 'twitter:data1'})
        if brand_meta:
            product['brand'] = brand_meta.get('content', '')

        return product

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """Scrape single product"""
        delay = self.delay * random.uniform(0.8, 1.2)
        time.sleep(max(0.3, delay))

        soup = self.get_page(url)
        if soup:
            return self.extract_product_data(soup, url)
        return None

    def get_product_urls(self, target: int = 10000) -> List[str]:
        """Get product URLs"""
        print(f"\n{'='*70}")
        print(f"COLLECTING {target:,} PRODUCT URLS")
        print(f"{'='*70}")

        product_urls = []
        page = 1

        while len(product_urls) < target:
            search_url = f"{self.base_url}/search/?q=&per_page=120&page={page}"

            soup = self.get_page(search_url)
            if not soup:
                print(f"  Page {page}: Failed to fetch")
                break

            products = soup.find_all('a', class_='m-catalogue-product-title')
            if not products:
                print(f"  Page {page}: No more products")
                break

            for product in products:
                href = product.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    product_urls.append(full_url)

                    if len(product_urls) >= target:
                        break

            print(f"  Page {page}: +{len(products)} products (Total: {len(product_urls):,})")
            page += 1
            time.sleep(0.5)

        product_urls = list(set(product_urls))[:target]

        print(f"\n{'='*70}")
        print(f"Collected {len(product_urls):,} unique product URLs")
        print(f"{'='*70}\n")

        return product_urls

    def scrape_products(self, product_urls: List[str]) -> List[Dict]:
        """Scrape products with concurrent workers"""
        products = []
        failed_urls = []

        self.stats['total'] = len(product_urls)
        self.stats['start_time'] = time.time()

        print(f"{'='*70}")
        print(f"SCRAPING {len(product_urls):,} PRODUCTS")
        print(f"{'='*70}")
        print(f"Workers: {self.workers}")
        print(f"Proxies: {len(self.proxy_manager.proxies) if self.proxy_manager else 0}")
        print(f"Delay: {self.delay}s")
        estimated_time = len(product_urls) * self.delay / self.workers / 60
        print(f"Estimated time: {estimated_time:.1f} minutes ({estimated_time/60:.2f} hours)")
        print(f"{'='*70}\n")

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_to_url = {
                executor.submit(self.scrape_single_product, url): url
                for url in product_urls
            }

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    product = future.result()
                    if product and product.get('name'):
                        with self.products_lock:
                            products.append(product)
                            self.stats['success'] += 1
                    else:
                        failed_urls.append(url)
                        with self.stats_lock:
                            self.stats['failed'] += 1
                except:
                    failed_urls.append(url)
                    with self.stats_lock:
                        self.stats['failed'] += 1

                # Progress
                completed = self.stats['success'] + self.stats['failed']
                if completed % 100 == 0 or completed == len(product_urls):
                    self.print_progress(completed, len(product_urls))

                # Save every 1000 products
                if self.stats['success'] % 1000 == 0 and self.stats['success'] > 0:
                    self.save_products(products, suffix=f"_progress_{self.stats['success']}")

        self.stats['end_time'] = time.time()

        # Save failed URLs
        if failed_urls:
            failed_file = self.output_dir / "failed_urls.txt"
            with open(failed_file, 'w') as f:
                f.write('\n'.join(failed_urls))
            print(f"\n⚠️  Failed URLs saved: {failed_file}")

        return products

    def print_progress(self, completed: int, total: int):
        """Print progress"""
        elapsed = time.time() - self.stats['start_time']
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = (total - completed) / rate if rate > 0 else 0

        print(f"Progress: {completed:,}/{total:,} ({100*completed/total:.1f}%) | "
              f"Success: {self.stats['success']:,} | Failed: {self.stats['failed']:,} | "
              f"Rate: {rate:.2f}/s | ETA: {remaining/60:.1f}m")

    def save_products(self, products: List[Dict], suffix: str = ""):
        """Save products"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON
        json_file = self.output_dir / f"products{suffix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved: {json_file} ({len(products):,} products)")

        # CSV
        csv_file = self.output_dir / f"products{suffix}_{timestamp}.csv"
        if products:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=products[0].keys())
                writer.writeheader()
                writer.writerows(products)

    def print_summary(self):
        """Print final summary"""
        elapsed = self.stats['end_time'] - self.stats['start_time']

        print(f"\n{'='*70}")
        print(f"TEST COMPLETE!")
        print(f"{'='*70}")
        print(f"Total products: {self.stats['total']:,}")
        print(f"Successfully scraped: {self.stats['success']:,} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"Failed: {self.stats['failed']:,} ({self.stats['failed']/self.stats['total']*100:.1f}%)")
        print(f"Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
        print(f"Average rate: {self.stats['success']/elapsed:.2f} products/second")
        print(f"Output: {self.output_dir.absolute()}")
        print(f"{'='*70}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Test scraper - 10k products with 10 proxies')
    parser.add_argument('--webshare-api-key', type=str, required=True, help='Webshare API key')
    parser.add_argument('--workers', type=int, default=10, help='Workers (default: 10)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay (default: 0.5s)')
    parser.add_argument('--target', type=int, default=10000, help='Target products (default: 10,000)')
    parser.add_argument('--output-dir', type=str, default='test_10k_data', help='Output directory')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"TEST SCRAPER - 10K PRODUCTS WITH 10 PROXIES")
    print(f"{'='*70}")
    print(f"Target: {args.target:,} products")
    print(f"Workers: {args.workers}")
    print(f"Delay: {args.delay}s")
    print(f"{'='*70}\n")

    # Initialize scraper
    scraper = TestScraper(
        output_dir=args.output_dir,
        workers=args.workers,
        delay=args.delay
    )

    # Setup proxies
    print("Setting up proxies...")
    scraper.proxy_manager = WebshareProxyManager(args.webshare_api_key)

    if not scraper.proxy_manager.fetch_proxies(limit=10):
        print("❌ Failed to fetch proxies. Exiting.")
        return

    if not scraper.proxy_manager.validate_all_proxies():
        print("❌ No working proxies. Exiting.")
        return

    # Get product URLs
    product_urls = scraper.get_product_urls(target=args.target)

    if not product_urls:
        print("❌ No product URLs found!")
        return

    # Scrape products
    products = scraper.scrape_products(product_urls)

    # Save final results
    scraper.save_products(products, suffix="_final")

    # Print summary
    scraper.print_summary()

    # Proxy stats
    scraper.proxy_manager.print_stats()

    print("✅ Test complete!")


if __name__ == '__main__':
    main()
