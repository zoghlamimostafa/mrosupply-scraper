#!/usr/bin/env python3
"""
Fast Concurrent MROSupply.com Product Scraper
Optimized for speed with concurrent requests and progress tracking
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
from proxy_manager import ProxyManager
from enhanced_headers import BrowserFingerprint


class FastMROSupplyScraper:
    """High-performance scraper with concurrent requests"""

    def __init__(self, output_dir: str = "scraped_data", max_workers: int = 10, use_proxies: bool = False,
                 delay_between_requests: float = 0.5):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.use_proxies = use_proxies
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
            'proxy_success': 0,
            'proxy_failed': 0,
        }

        # Proxy manager
        self.proxy_manager = None
        if self.use_proxies:
            print("Initializing proxy manager...")
            self.proxy_manager = ProxyManager(proxy_types=['http', 'socks5'])

        # Session configuration with realistic browser headers
        self.session = requests.Session()
        # Set initial headers - will be updated per request for more realism
        realistic_headers = BrowserFingerprint.get_realistic_headers()
        self.session.headers.update(realistic_headers)

        # Enable cookie persistence (looks more like a real browser)
        self.session.cookies.set('sessionid', f'session_{int(time.time())}', domain='.mrosupply.com')

    def get_page(self, url: str, max_retries: int = 3, timeout: int = 15, referer: str = None) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with retry logic, proxy rotation, and rate limit handling"""
        for attempt in range(max_retries):
            proxy = None
            try:
                # Update headers with rotation and referer for each request (more realistic)
                request_headers = BrowserFingerprint.get_realistic_headers(referer=referer)

                # Get proxy if enabled
                if self.use_proxies and self.proxy_manager:
                    proxy = self.proxy_manager.get_random_proxy()

                # Make request with updated headers
                if proxy:
                    response = self.session.get(url, proxies=proxy, timeout=timeout, headers=request_headers)
                else:
                    response = self.session.get(url, timeout=timeout, headers=request_headers)

                response.raise_for_status()

                # Mark proxy as successful
                if proxy:
                    self.proxy_manager.mark_proxy_success(proxy)
                    with self.stats_lock:
                        self.stats['proxy_success'] += 1

                return BeautifulSoup(response.text, 'html.parser')

            except requests.HTTPError as e:
                # Mark proxy as failed
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                    with self.stats_lock:
                        self.stats['proxy_failed'] += 1

                if e.response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    print(f"Rate limited! Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    if attempt < max_retries - 1:
                        continue
                print(f"Failed: {url[:80]}... - {str(e)[:50]}")
                return None

            except requests.RequestException as e:
                # Mark proxy as failed
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                    with self.stats_lock:
                        self.stats['proxy_failed'] += 1

                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Short delay before retry with different proxy
                else:
                    print(f"Failed: {url[:80]}... - {str(e)[:50]}")
                    return None

        return None

    def extract_product_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract all product data from a product page (optimized)"""
        product_data = {
            'url': url,
            'name': '',
            'brand': '',
            'mpn': '',
            'sku': '',
            'price': '',
            'price_note': '',
            'category': '',
            'description': '',
            'images': [],
            'specifications': {},
            'additional_description': '',
            'documents': [],
            'related_products': [],
            'availability': '',
        }

        # Extract from JSON-LD (fastest method)
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
            except (json.JSONDecodeError, KeyError):
                pass

        # Extract brand
        brand_meta = soup.find('meta', {'name': 'twitter:data1'})
        if brand_meta:
            product_data['brand'] = brand_meta.get('content', brand_meta.get('value', ''))

        # Extract price from page (backup)
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

        # Extract additional description
        additional_desc_section = soup.find('div', id='additionalDescription')
        if additional_desc_section:
            desc_body = additional_desc_section.find('div', class_='m-accordion--item--body')
            if desc_body:
                desc_text = desc_body.get_text(separator='\n', strip=True)
                product_data['additional_description'] = desc_text

        # Extract documents
        doc_section = soup.find_all('div', class_='m-accordion--item')
        for section in doc_section:
            section_head = section.find('button', class_='m-accordion--item--head')
            if section_head and 'Documents / Software' in section_head.get_text():
                doc_body = section.find('div', class_='m-accordion--item--body')
                if doc_body:
                    doc_items = doc_body.find_all('div', class_='documents--item')
                    for item in doc_items:
                        link = item.find('a')
                        if link:
                            doc_url = link.get('href', '')
                            doc_name = link.get_text(strip=True)
                            if doc_url:
                                product_data['documents'].append({
                                    'name': doc_name,
                                    'url': doc_url
                                })
                break

        return product_data

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """Scrape a single product page with rate limit protection and human-like behavior"""
        # Add configurable delay to avoid rate limits and bans
        # More human-like randomization (±30% variation)
        random_variation = random.uniform(-0.3, 0.3)
        delay = self.delay_between_requests * (1 + random_variation)
        delay = max(0.5, delay)  # Never less than 0.5s
        time.sleep(delay)

        # Add referer to simulate navigation from search page (more realistic)
        referer = f"{self.base_url}/search/"
        soup = self.get_page(url, referer=referer)
        if soup:
            return self.extract_product_data(soup, url)
        return None

    def get_product_urls_from_search(self, per_page: int = 120, max_pages: Optional[int] = None) -> List[str]:
        """Get all product URLs from search results (fast)"""
        product_urls = []
        page = 1

        print(f"Fetching product URLs from search...")

        # Temporarily disable proxies for search page fetching (more reliable)
        original_proxy_setting = self.use_proxies
        if self.use_proxies:
            print("Note: Using direct connection for search pages (more reliable)")
            self.use_proxies = False

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
            time.sleep(0.3)  # Small delay for search pages

        # Re-enable proxies for product scraping
        self.use_proxies = original_proxy_setting
        if self.use_proxies:
            print(f"Proxies re-enabled for product scraping\n")

        # Remove duplicates
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
        print(f"Delay between requests: {self.delay_between_requests}s")
        estimated_time = len(product_urls) * self.delay_between_requests / self.max_workers / 60
        print(f"Estimated time: {estimated_time:.1f} minutes")
        print(f"{'='*70}\n")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.scrape_single_product, url): url
                for url in product_urls
            }

            # Process completed tasks
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
                    print(f"Exception for {url}: {e}")
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

        # Print final statistics
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
        print(f"Total time: {elapsed/60:.2f} minutes ({elapsed:.1f} seconds)")
        print(f"Average rate: {self.stats['success']/elapsed:.2f} products/second")

        if self.use_proxies and self.proxy_manager:
            print(f"\nProxy Statistics:")
            print(f"  Successful proxy requests: {self.stats['proxy_success']}")
            print(f"  Failed proxy requests: {self.stats['proxy_failed']}")
            if self.stats['proxy_success'] + self.stats['proxy_failed'] > 0:
                success_rate = self.stats['proxy_success'] / (self.stats['proxy_success'] + self.stats['proxy_failed']) * 100
                print(f"  Proxy success rate: {success_rate:.1f}%")
            self.proxy_manager.print_stats()

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
        print(f"Saved {len(products)} products to {json_file}")

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
                        'additional_description': p['additional_description'],
                        'documents': json.dumps(p['documents']),
                        'availability': p['availability'],
                    }
                    flattened_products.append(flat)

                if flattened_products:
                    writer = csv.DictWriter(f, fieldnames=flattened_products[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_products)
            print(f"Saved {len(products)} products to {csv_file}")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Fast scraper for MROSupply.com with proxy support')
    parser.add_argument('--max-pages', type=int, help='Maximum number of search pages')
    parser.add_argument('--max-products', type=int, help='Maximum number of products to scrape')
    parser.add_argument('--workers', type=int, default=2, help='Number of concurrent workers (default: 2 - SAFE, no rate limits)')
    parser.add_argument('--output-dir', type=str, default='scraped_data', help='Output directory')
    parser.add_argument('--estimate', action='store_true', help='Only estimate total products, don\'t scrape')
    parser.add_argument('--use-proxies', action='store_true', help='Enable proxy rotation to distribute load')
    parser.add_argument('--validate-proxies', type=int, default=50, help='Number of proxies to validate (default: 50)')
    parser.add_argument('--delay', type=float, default=1.5, help='Delay between requests in seconds (default: 1.5 - SAFE, prevents bans)')

    args = parser.parse_args()

    scraper = FastMROSupplyScraper(
        output_dir=args.output_dir,
        max_workers=args.workers,
        use_proxies=args.use_proxies,
        delay_between_requests=args.delay
    )

    # Initialize proxies if enabled
    if args.use_proxies:
        print("\n" + "="*70)
        print("PROXY SETUP")
        print("="*70)
        scraper.proxy_manager.fetch_proxies()
        scraper.proxy_manager.validate_proxies(max_test=args.validate_proxies)
        print("="*70 + "\n")

        if not scraper.proxy_manager.working_proxies and not scraper.proxy_manager.proxies:
            print("WARNING: No proxies available. Continuing without proxies...")
            scraper.use_proxies = False

    # Get product URLs
    product_urls = scraper.get_product_urls_from_search(max_pages=args.max_pages)

    if args.estimate:
        print(f"\n{'='*70}")
        print(f"ESTIMATION")
        print(f"{'='*70}")
        print(f"Total products found: {len(product_urls)}")
        print(f"With {args.workers} workers at ~5 products/second:")
        print(f"  Estimated time: {len(product_urls)/5/60:.1f} minutes ({len(product_urls)/5/3600:.2f} hours)")
        print(f"With {args.workers} workers at ~10 products/second (aggressive):")
        print(f"  Estimated time: {len(product_urls)/10/60:.1f} minutes ({len(product_urls)/10/3600:.2f} hours)")
        print(f"{'='*70}\n")
        return

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
