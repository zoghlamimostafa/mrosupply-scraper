#!/usr/bin/env python3
"""
Production Scraper for mrosupply.com with Webshare Proxies
- Tests proxies on 100 products first
- Scrapes all 1,508,692 products
- Auto-saves progress every 500 products
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
    """Fetch and manage proxies from Webshare API with validation"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.all_proxies = []
        self.working_proxies = []
        self.failed_proxies = []
        self.proxy_index = 0
        self.proxy_lock = Lock()
        self.proxy_stats = {}  # Track success/failure per proxy

    def fetch_proxies(self):
        """Fetch all available proxies from Webshare API"""
        print("Fetching proxies from Webshare API...")

        url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100"
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
                    self.all_proxies.append(proxy_obj)
                    self.proxy_stats[proxy_obj['id']] = {'success': 0, 'failed': 0}

            print(f"✅ Successfully fetched {len(self.all_proxies)} proxies from Webshare")
            return len(self.all_proxies) > 0

        except Exception as e:
            print(f"❌ Failed to fetch proxies from Webshare: {e}")
            return False

    def test_proxy(self, proxy: dict, test_url: str = "https://www.mrosupply.com") -> bool:
        """Test if a proxy works"""
        try:
            response = requests.get(
                test_url,
                proxies=proxy,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except:
            return False

    def validate_proxies(self, test_count: int = 3):
        """Validate all proxies by testing them"""
        print(f"\n{'='*70}")
        print(f"VALIDATING PROXIES")
        print(f"{'='*70}")
        print(f"Testing {len(self.all_proxies)} proxies (each tested {test_count} times)...")

        for i, proxy in enumerate(self.all_proxies, 1):
            success_count = 0
            for _ in range(test_count):
                if self.test_proxy(proxy):
                    success_count += 1
                time.sleep(0.2)

            if success_count >= 2:  # At least 2 out of 3 successes
                self.working_proxies.append(proxy)
                print(f"  [{i}/{len(self.all_proxies)}] ✅ {proxy['address']} - Working ({success_count}/{test_count})")
            else:
                self.failed_proxies.append(proxy)
                print(f"  [{i}/{len(self.all_proxies)}] ❌ {proxy['address']} - Failed ({success_count}/{test_count})")

        print(f"\n{'='*70}")
        print(f"Validation Complete:")
        print(f"  Working proxies: {len(self.working_proxies)}")
        print(f"  Failed proxies: {len(self.failed_proxies)}")
        print(f"{'='*70}\n")

        return len(self.working_proxies) > 0

    def get_next_proxy(self):
        """Get next working proxy in rotation"""
        if not self.working_proxies:
            return None

        with self.proxy_lock:
            proxy = self.working_proxies[self.proxy_index % len(self.working_proxies)]
            self.proxy_index += 1
            return proxy

    def mark_proxy_success(self, proxy: dict):
        """Mark a proxy as successful"""
        if proxy and proxy['id'] in self.proxy_stats:
            self.proxy_stats[proxy['id']]['success'] += 1

    def mark_proxy_failed(self, proxy: dict):
        """Mark a proxy as failed"""
        if proxy and proxy['id'] in self.proxy_stats:
            self.proxy_stats[proxy['id']]['failed'] += 1

    def get_stats(self):
        """Get proxy statistics"""
        total_success = sum(s['success'] for s in self.proxy_stats.values())
        total_failed = sum(s['failed'] for s in self.proxy_stats.values())
        return {
            'total_proxies': len(self.all_proxies),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'total_success': total_success,
            'total_failed': total_failed,
            'success_rate': (total_success / (total_success + total_failed) * 100) if (total_success + total_failed) > 0 else 0
        }


class ProductionScraper:
    """Production scraper for all 1.5M products"""

    def __init__(self, output_dir: str = "production_data", max_workers: int = 12,
                 webshare_api_key: str = None, delay: float = 0.5):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
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

        # Proxy manager
        self.proxy_manager = None
        self.use_proxies = False

        if webshare_api_key:
            self.proxy_manager = WebshareProxyManager(webshare_api_key)

        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
        })

    def initialize_proxies(self):
        """Fetch and validate proxies"""
        if not self.proxy_manager:
            return False

        print(f"\n{'='*70}")
        print("PROXY INITIALIZATION")
        print(f"{'='*70}")

        if not self.proxy_manager.fetch_proxies():
            print("❌ Failed to fetch proxies. Will run without proxies.")
            return False

        if not self.proxy_manager.validate_proxies():
            print("❌ No working proxies found. Will run without proxies.")
            return False

        self.use_proxies = True
        print("✅ Proxies ready for use!\n")
        return True

    def test_proxies_on_products(self, test_count: int = 100):
        """Test proxies by scraping 100 products"""
        print(f"\n{'='*70}")
        print(f"TESTING PROXIES ON {test_count} PRODUCTS")
        print(f"{'='*70}")

        # Get test product URLs
        product_urls = self.get_product_urls_from_search(max_pages=1)
        test_urls = product_urls[:test_count]

        print(f"Testing with {len(test_urls)} products...\n")

        # Scrape test products
        test_products = self.scrape_products_concurrent(test_urls)

        # Show results
        success_rate = (len(test_products) / len(test_urls) * 100) if test_urls else 0

        print(f"\n{'='*70}")
        print(f"PROXY TEST RESULTS")
        print(f"{'='*70}")
        print(f"Products tested: {len(test_urls)}")
        print(f"Successfully scraped: {len(test_products)}")
        print(f"Success rate: {success_rate:.1f}%")

        if self.use_proxies:
            proxy_stats = self.proxy_manager.get_stats()
            print(f"\nProxy Statistics:")
            print(f"  Working proxies: {proxy_stats['working_proxies']}")
            print(f"  Requests success rate: {proxy_stats['success_rate']:.1f}%")

        print(f"{'='*70}\n")

        if success_rate < 50:
            print("⚠️  WARNING: Success rate is below 50%. Consider checking proxies.")
            response = input("Continue anyway? [y/N]: ").lower()
            if response != 'y':
                return False

        return True

    def get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with proxy rotation"""
        for attempt in range(max_retries):
            proxy = None
            try:
                if self.use_proxies and self.proxy_manager:
                    proxy = self.proxy_manager.get_next_proxy()

                if proxy:
                    response = self.session.get(url, proxies=proxy, timeout=15)
                else:
                    response = self.session.get(url, timeout=15)

                response.raise_for_status()

                if proxy:
                    self.proxy_manager.mark_proxy_success(proxy)

                return BeautifulSoup(response.text, 'html.parser')

            except Exception as e:
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)

                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    return None

        return None

    def extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product data"""
        product_data = {
            'url': url,
            'name': '',
            'brand': '',
            'mpn': '',
            'sku': '',
            'price': '',
            'category': '',
            'description': '',
            'images': [],
            'specifications': {},
            'availability': '',
        }

        # Extract from JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if data.get('@type') == 'Product':
                    product_data['name'] = data.get('name', '')
                    product_data['description'] = data.get('description', '')
                    product_data['category'] = data.get('category', '')
                    if data.get('image'):
                        product_data['images'].append(data['image'])

                    offers = data.get('offers', [])
                    if isinstance(offers, list) and offers:
                        offer = offers[0]
                        product_data['sku'] = str(offer.get('sku', ''))
                        product_data['mpn'] = offer.get('mpn', '')
                        product_data['price'] = f"${offer.get('price', '')}"
                        product_data['availability'] = offer.get('availability', '')
            except:
                pass

        # Extract brand
        brand_meta = soup.find('meta', {'name': 'twitter:data1'})
        if brand_meta:
            product_data['brand'] = brand_meta.get('content', '')

        # Extract specifications
        spec_sections = soup.find_all('div', class_='m-accordion--item')
        for spec_section in spec_sections:
            spec_head = spec_section.find('button', class_='m-accordion--item--head')
            if spec_head and 'SPECIFICATION' in spec_head.get_text():
                spec_body = spec_section.find('div', class_='m-accordion--item--body')
                if spec_body:
                    grid_table = spec_body.find('div', class_='o-grid-table')
                    if grid_table:
                        grid_items = grid_table.find_all('div', class_='o-grid-item')
                        for item in grid_items:
                            key_elem = item.find('p', class_='key')
                            value_elem = item.find('p', class_='value')
                            if key_elem and value_elem:
                                key = key_elem.get_text(strip=True)
                                value = value_elem.get_text(strip=True)
                                if key and value:
                                    product_data['specifications'][key] = value
                break

        return product_data

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """Scrape a single product"""
        delay = self.delay * random.uniform(0.8, 1.2)
        time.sleep(max(0.3, delay))

        soup = self.get_page(url)
        if soup:
            return self.extract_product_data(soup, url)
        return None

    def get_product_urls_from_search(self, per_page: int = 120, max_pages: Optional[int] = None) -> List[str]:
        """Get all product URLs from search"""
        product_urls = []
        page = 1
        consecutive_empty = 0

        print(f"\n{'='*70}")
        print("PHASE 1: COLLECTING PRODUCT URLS")
        print(f"{'='*70}")

        while True:
            if max_pages and page > max_pages:
                break

            search_url = f"{self.base_url}/search/?q=&per_page={per_page}&page={page}"

            soup = self.get_page(search_url)
            if not soup:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
                time.sleep(2)
                continue

            products = soup.find_all('a', class_='m-catalogue-product-title')
            if not products:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print(f"  No more products after page {page}")
                    break
                continue
            else:
                consecutive_empty = 0

            for product in products:
                href = product.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    product_urls.append(full_url)

            print(f"  Page {page}: +{len(products)} products (Total: {len(product_urls):,})")
            page += 1
            time.sleep(0.5)

        product_urls = list(set(product_urls))
        print(f"\n{'='*70}")
        print(f"URL Collection Complete: {len(product_urls):,} unique products")
        print(f"{'='*70}\n")
        return product_urls

    def scrape_products_concurrent(self, product_urls: List[str]) -> List[Dict]:
        """Scrape products with concurrent workers"""
        products = []
        failed_urls = []

        self.stats['total'] = len(product_urls)
        self.stats['start_time'] = time.time()

        print(f"\n{'='*70}")
        print(f"PHASE 2: SCRAPING PRODUCTS")
        print(f"{'='*70}")
        print(f"Total products: {len(product_urls):,}")
        print(f"Workers: {self.max_workers}")
        print(f"Using proxies: {'YES' if self.use_proxies else 'NO'}")
        if self.use_proxies:
            print(f"Active proxies: {len(self.proxy_manager.working_proxies)}")
        print(f"Delay: {self.delay}s")
        estimated_time = len(product_urls) * self.delay / self.max_workers / 60
        print(f"Estimated time: {estimated_time:.1f} minutes ({estimated_time/60:.1f} hours)")
        print(f"{'='*70}\n")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
                except Exception as e:
                    failed_urls.append(url)
                    with self.stats_lock:
                        self.stats['failed'] += 1

                # Progress update
                completed = self.stats['success'] + self.stats['failed']
                if completed % 100 == 0 or completed == len(product_urls):
                    self.print_progress(completed, len(product_urls))

                # Save incrementally every 500 products
                if self.stats['success'] % 500 == 0 and self.stats['success'] > 0:
                    self.save_products(products, suffix=f"_progress_{self.stats['success']}")

        self.stats['end_time'] = time.time()

        # Save failed URLs
        if failed_urls:
            failed_file = self.output_dir / f"failed_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(failed_file, 'w') as f:
                f.write('\n'.join(failed_urls))
            print(f"\n⚠️  Failed URLs saved to: {failed_file}")

        return products

    def print_progress(self, completed: int, total: int):
        """Print progress"""
        elapsed = time.time() - self.stats['start_time']
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = (total - completed) / rate if rate > 0 else 0

        print(f"Progress: {completed:,}/{total:,} ({100*completed/total:.1f}%) | "
              f"Success: {self.stats['success']:,} | Failed: {self.stats['failed']:,} | "
              f"Rate: {rate:.2f}/s | ETA: {remaining/60:.1f}m ({remaining/3600:.1f}h)")

    def save_products(self, products: List[Dict], suffix: str = ""):
        """Save products to JSON and CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_file = self.output_dir / f"products{suffix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Saved: {json_file} ({len(products):,} products)")

        # Save CSV
        csv_file = self.output_dir / f"products{suffix}_{timestamp}.csv"
        if products:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                flattened_products = []
                for p in products:
                    flat = {
                        'url': p['url'],
                        'name': p['name'],
                        'brand': p['brand'],
                        'mpn': p['mpn'],
                        'sku': p['sku'],
                        'price': p['price'],
                        'category': p['category'],
                        'description': p['description'],
                        'images': '|'.join(p['images']),
                        'specifications': json.dumps(p['specifications']),
                        'availability': p['availability'],
                    }
                    flattened_products.append(flat)

                if flattened_products:
                    writer = csv.DictWriter(f, fieldnames=flattened_products[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_products)

    def print_final_summary(self):
        """Print final summary"""
        elapsed = self.stats['end_time'] - self.stats['start_time']

        print(f"\n{'='*70}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'='*70}")
        print(f"Total products: {self.stats['total']:,}")
        print(f"Successfully scraped: {self.stats['success']:,} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"Failed: {self.stats['failed']:,} ({self.stats['failed']/self.stats['total']*100:.1f}%)")
        print(f"Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
        print(f"Average rate: {self.stats['success']/elapsed:.2f} products/second")

        if self.use_proxies:
            proxy_stats = self.proxy_manager.get_stats()
            print(f"\nProxy Statistics:")
            print(f"  Total proxies: {proxy_stats['total_proxies']}")
            print(f"  Working proxies: {proxy_stats['working_proxies']}")
            print(f"  Success rate: {proxy_stats['success_rate']:.1f}%")

        print(f"\nOutput directory: {self.output_dir.absolute()}")
        print(f"{'='*70}\n")

    def run(self, test_first: bool = True):
        """Run the complete scraping process"""
        try:
            # Initialize proxies
            if self.proxy_manager:
                self.initialize_proxies()

            # Test proxies on 100 products first
            if test_first and self.use_proxies:
                if not self.test_proxies_on_products(test_count=100):
                    print("❌ Proxy test failed. Exiting.")
                    return False

                print("✅ Proxy test passed! Starting full scrape...\n")
                time.sleep(3)

            # Get all product URLs
            product_urls = self.get_product_urls_from_search()

            if not product_urls:
                print("❌ No product URLs found!")
                return False

            print(f"\n🎯 Target: {len(product_urls):,} products")
            print(f"📊 Estimated time: {len(product_urls) * self.delay / self.max_workers / 3600:.1f} hours")
            print(f"\nStarting in 5 seconds... (Ctrl+C to cancel)\n")

            for i in range(5, 0, -1):
                print(f"  Starting in {i}...")
                time.sleep(1)

            # Scrape all products
            products = self.scrape_products_concurrent(product_urls)

            # Save final results
            self.save_products(products, suffix="_final")

            # Print summary
            self.print_final_summary()

            return True

        except KeyboardInterrupt:
            print(f"\n\n{'='*70}")
            print(f"INTERRUPTED BY USER")
            print(f"{'='*70}")
            self.stats['end_time'] = time.time()
            self.print_final_summary()
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Production scraper with Webshare proxy support')
    parser.add_argument('--workers', type=int, default=12, help='Number of workers (default: 12)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (default: 0.5)')
    parser.add_argument('--output-dir', type=str, default='production_data', help='Output directory')
    parser.add_argument('--webshare-api-key', type=str, required=True, help='Webshare API key (REQUIRED)')
    parser.add_argument('--no-test', action='store_true', help='Skip proxy testing on 100 products')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"MROSUPPLY.COM PRODUCTION SCRAPER")
    print(f"{'='*70}")
    print(f"Target: 1,508,692 products")
    print(f"Workers: {args.workers}")
    print(f"Delay: {args.delay}s")
    print(f"{'='*70}\n")

    scraper = ProductionScraper(
        output_dir=args.output_dir,
        max_workers=args.workers,
        webshare_api_key=args.webshare_api_key,
        delay=args.delay
    )

    success = scraper.run(test_first=not args.no_test)

    if success:
        print("✅ Scraping completed successfully!")
    else:
        print("⚠️  Scraping ended early")


if __name__ == '__main__':
    main()
