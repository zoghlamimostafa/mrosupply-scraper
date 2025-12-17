#!/usr/bin/env python3
"""
Fast Concurrent MROSupply.com Product Scraper with Webshare Proxies
Uses Webshare API to get proxies automatically
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
    """Fetch and manage proxies from Webshare API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.proxies = []
        self.proxy_index = 0
        self.proxy_lock = Lock()

    def fetch_proxies(self):
        """Fetch proxies from Webshare API"""
        print("Fetching proxies from Webshare API...")

        url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100"
        headers = {
            "Authorization": f"Token {self.api_key}"
        }

        try:
            response = requests.get(url, headers=headers)
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
                    self.proxies.append({
                        'http': proxy_url,
                        'https': proxy_url,
                        'address': proxy_address
                    })

            print(f"✅ Successfully fetched {len(self.proxies)} proxies from Webshare")
            return len(self.proxies) > 0

        except Exception as e:
            print(f"❌ Failed to fetch proxies from Webshare: {e}")
            return False

    def get_next_proxy(self):
        """Get next proxy in rotation"""
        if not self.proxies:
            return None

        with self.proxy_lock:
            proxy = self.proxies[self.proxy_index % len(self.proxies)]
            self.proxy_index += 1
            return proxy


class FastMROSupplyScraper:
    """High-performance scraper with Webshare proxy support"""

    def __init__(self, output_dir: str = "scraped_data", max_workers: int = 10,
                 webshare_api_key: str = None, delay_between_requests: float = 0.5):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
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
            print(f"\n{'='*70}")
            print("Initializing Webshare Proxies...")
            print(f"{'='*70}")
            self.proxy_manager = WebshareProxyManager(webshare_api_key)
            if self.proxy_manager.fetch_proxies():
                self.use_proxies = True
                print(f"{'='*70}\n")
            else:
                print("Continuing without proxies...")
                print(f"{'='*70}\n")

        # Session with realistic headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_page(self, url: str, max_retries: int = 3, timeout: int = 15) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with retry logic and proxy rotation"""
        for attempt in range(max_retries):
            proxy = None
            try:
                # Get proxy if enabled
                if self.use_proxies and self.proxy_manager:
                    proxy = self.proxy_manager.get_next_proxy()

                # Make request
                if proxy:
                    response = self.session.get(url, proxies=proxy, timeout=timeout)
                else:
                    response = self.session.get(url, timeout=timeout)

                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')

            except requests.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    print(f"Rate limited! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return None

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    return None

        return None

    def extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract all product data from a product page"""
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

        # Extract price (backup)
        if not product_data['price']:
            price_elem = soup.find('p', class_='price')
            if price_elem:
                product_data['price'] = price_elem.get_text(strip=True)

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
        """Scrape a single product with delay"""
        # Random delay to avoid rate limits
        delay = self.delay_between_requests * random.uniform(0.8, 1.2)
        time.sleep(max(0.5, delay))

        soup = self.get_page(url)
        if soup:
            return self.extract_product_data(soup, url)
        return None

    def get_product_urls_from_search(self, per_page: int = 120, max_pages: Optional[int] = None) -> List[str]:
        """Get all product URLs from search results"""
        product_urls = []
        page = 1

        print(f"Fetching product URLs from search...")

        while True:
            if max_pages and page > max_pages:
                break

            search_url = f"{self.base_url}/search/?q=&per_page={per_page}&page={page}"

            soup = self.get_page(search_url)
            if not soup:
                break

            products = soup.find_all('a', class_='m-catalogue-product-title')
            if not products:
                print(f"No more products on page {page}")
                break

            for product in products:
                href = product.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    product_urls.append(full_url)

            print(f"Page {page}: Found {len(products)} products (Total: {len(product_urls)})")
            page += 1
            time.sleep(0.5)

        product_urls = list(set(product_urls))
        print(f"\nTotal unique products found: {len(product_urls)}")
        return product_urls

    def scrape_products_concurrent(self, product_urls: List[str]) -> List[Dict]:
        """Scrape products using concurrent workers"""
        products = []
        failed_urls = []

        self.stats['total'] = len(product_urls)
        self.stats['start_time'] = time.time()

        print(f"\n{'='*70}")
        print(f"Starting concurrent scraping with {self.max_workers} workers")
        print(f"Total products to scrape: {len(product_urls)}")
        print(f"Using proxies: {'YES' if self.use_proxies else 'NO'}")
        print(f"Delay between requests: {self.delay_between_requests}s")
        estimated_time = len(product_urls) * self.delay_between_requests / self.max_workers / 60
        print(f"Estimated time: {estimated_time:.1f} minutes")
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
                    if product:
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
                if completed % 50 == 0 or completed == len(product_urls):
                    self.print_progress(completed, len(product_urls))

                # Save incrementally
                if len(products) % 100 == 0 and len(products) > 0:
                    self.save_products(products, suffix=f"_progress_{len(products)}")

        self.stats['end_time'] = time.time()
        self.print_final_stats(failed_urls)

        return products

    def print_progress(self, completed: int, total: int):
        """Print progress statistics"""
        elapsed = time.time() - self.stats['start_time']
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = (total - completed) / rate if rate > 0 else 0

        print(f"Progress: {completed}/{total} ({100*completed/total:.1f}%) | "
              f"Success: {self.stats['success']} | Failed: {self.stats['failed']} | "
              f"Rate: {rate:.1f}/s | ETA: {remaining/60:.1f}m")

    def print_final_stats(self, failed_urls: List[str]):
        """Print final scraping statistics"""
        elapsed = self.stats['end_time'] - self.stats['start_time']

        print(f"\n{'='*70}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Total products: {self.stats['total']}")
        print(f"Successfully scraped: {self.stats['success']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Total time: {elapsed/60:.2f} minutes")
        print(f"Average rate: {self.stats['success']/elapsed:.2f} products/second")
        print(f"{'='*70}\n")

        if failed_urls:
            failed_file = self.output_dir / "failed_urls.txt"
            with open(failed_file, 'w') as f:
                f.write('\n'.join(failed_urls))
            print(f"Failed URLs saved to: {failed_file}\n")

    def save_products(self, products: List[Dict], suffix: str = "") -> None:
        """Save products to JSON and CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save as JSON
        json_file = self.output_dir / f"products{suffix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(products)} products to {json_file}")

        # Save as CSV
        csv_file = self.output_dir / f"products{suffix}.csv"
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


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Fast scraper with Webshare proxy support')
    parser.add_argument('--max-pages', type=int, help='Maximum number of search pages')
    parser.add_argument('--max-products', type=int, help='Maximum number of products to scrape')
    parser.add_argument('--workers', type=int, default=2, help='Number of concurrent workers (default: 2)')
    parser.add_argument('--output-dir', type=str, default='scraped_data', help='Output directory')
    parser.add_argument('--delay', type=float, default=1.5, help='Delay between requests in seconds (default: 1.5)')
    parser.add_argument('--webshare-api-key', type=str, help='Webshare API key for proxy support')

    args = parser.parse_args()

    scraper = FastMROSupplyScraper(
        output_dir=args.output_dir,
        max_workers=args.workers,
        webshare_api_key=args.webshare_api_key,
        delay_between_requests=args.delay
    )

    # Get product URLs
    product_urls = scraper.get_product_urls_from_search(max_pages=args.max_pages)

    if args.max_products:
        product_urls = product_urls[:args.max_products]
        print(f"Limited to {len(product_urls)} products")

    # Scrape products
    products = scraper.scrape_products_concurrent(product_urls)

    # Save final results
    scraper.save_products(products, suffix="_final")

    print("\n=== ALL DONE ===\n")


if __name__ == '__main__':
    main()
