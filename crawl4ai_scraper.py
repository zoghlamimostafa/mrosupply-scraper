#!/usr/bin/env python3
"""
Crawl4AI-based Scraper for mrosupply.com
Uses sitemap XMLs (1-151) and Webshare proxies
"""

import json
import csv
import time
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class WebshareProxyManager:
    """Manage Webshare proxies"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.working_proxies = []
        self.proxy_index = 0
        self.proxy_lock = Lock()
        self.proxy_stats = {}

    def fetch_proxies(self, limit: int = 100):
        """Fetch proxies from Webshare API"""
        print(f"Fetching up to {limit} proxies from Webshare API...")

        url = f"https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size={limit}"
        headers = {"Authorization": f"Token {self.api_key}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

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
                    self.working_proxies.append(proxy_obj)
                    self.proxy_stats[proxy_obj['id']] = {'success': 0, 'failed': 0}

            print(f"✅ Fetched {len(self.working_proxies)} proxies")
            return len(self.working_proxies) > 0

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

    def validate_proxies(self):
        """Validate all proxies"""
        print(f"\n{'='*70}")
        print(f"VALIDATING {len(self.working_proxies)} PROXIES")
        print(f"{'='*70}")

        working = []

        for i, proxy in enumerate(self.working_proxies, 1):
            print(f"  [{i}/{len(self.working_proxies)}] Testing {proxy['address']}...", end=' ')

            success_count = 0
            for _ in range(3):
                if self.test_proxy(proxy):
                    success_count += 1
                time.sleep(0.2)

            if success_count >= 2:
                working.append(proxy)
                print(f"✅ ({success_count}/3)")
            else:
                print(f"❌ ({success_count}/3)")

        self.working_proxies = working

        print(f"\n{'='*70}")
        print(f"Working proxies: {len(working)}")
        print(f"{'='*70}\n")

        return len(working) > 0

    def get_next_proxy(self):
        """Get next proxy"""
        if not self.working_proxies:
            return None

        with self.proxy_lock:
            proxy = self.working_proxies[self.proxy_index % len(self.working_proxies)]
            self.proxy_index += 1
            return proxy

    def mark_success(self, proxy: dict):
        if proxy and proxy['id'] in self.proxy_stats:
            self.proxy_stats[proxy['id']]['success'] += 1

    def mark_failed(self, proxy: dict):
        if proxy and proxy['id'] in self.proxy_stats:
            self.proxy_stats[proxy['id']]['failed'] += 1


class SitemapScraper:
    """Scraper using sitemap XML files"""

    def __init__(self, output_dir: str = "sitemap_scraped_data", workers: int = 10, delay: float = 0.5):
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

    def parse_sitemap_file(self, sitemap_file: str) -> List[str]:
        """Parse a local sitemap XML file"""
        product_urls = []

        try:
            tree = ET.parse(sitemap_file)
            root = tree.getroot()

            # Handle XML namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url_elem in root.findall('ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    product_urls.append(loc.text)

            print(f"  ✅ Parsed {sitemap_file}: {len(product_urls)} URLs")

        except Exception as e:
            print(f"  ❌ Error parsing {sitemap_file}: {e}")

        return product_urls

    def download_sitemap_from_web(self, sitemap_num: int) -> Optional[List[str]]:
        """Download and parse sitemap from web"""
        sitemap_url = f"{self.base_url}/sitemap-product-{sitemap_num}.xml"
        product_urls = []

        try:
            print(f"  Downloading sitemap {sitemap_num}...", end=' ')

            response = requests.get(sitemap_url, timeout=15)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Handle XML namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url_elem in root.findall('ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    product_urls.append(loc.text)

            print(f"✅ {len(product_urls)} URLs")

        except Exception as e:
            print(f"❌ Error: {e}")

        return product_urls

    def collect_urls_from_sitemaps(self, sitemap_range: tuple = (1, 151), local_dir: str = None) -> List[str]:
        """Collect all URLs from sitemaps"""
        print(f"\n{'='*70}")
        print(f"COLLECTING URLS FROM SITEMAPS {sitemap_range[0]}-{sitemap_range[1]}")
        print(f"{'='*70}")

        all_urls = []

        for sitemap_num in range(sitemap_range[0], sitemap_range[1] + 1):
            # Try local file first
            if local_dir:
                local_file = Path(local_dir) / f"sitemap-product-{sitemap_num}.xml"
                if local_file.exists():
                    urls = self.parse_sitemap_file(str(local_file))
                    all_urls.extend(urls)
                    continue

            # Download from web
            urls = self.download_sitemap_from_web(sitemap_num)
            if urls:
                all_urls.extend(urls)

            time.sleep(0.5)  # Be polite

        # Remove duplicates
        all_urls = list(set(all_urls))

        print(f"\n{'='*70}")
        print(f"Total unique URLs collected: {len(all_urls):,}")
        print(f"{'='*70}\n")

        return all_urls

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

            except Exception:
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
                    product['name'] = data.get('name', '')
                    product['description'] = data.get('description', '')
                    product['category'] = data.get('category', '')

                    if data.get('image'):
                        product['images'].append(data['image'])

                    offers = data.get('offers', [])
                    if isinstance(offers, list) and offers:
                        offer = offers[0]
                        product['sku'] = str(offer.get('sku', ''))
                        product['mpn'] = offer.get('mpn', '')
                        product['price'] = f"${offer.get('price', '')}"
                        product['availability'] = offer.get('availability', '')
            except:
                pass

        # Brand
        brand_meta = soup.find('meta', {'name': 'twitter:data1'})
        if brand_meta:
            product['brand'] = brand_meta.get('content', '')

        # Specifications
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
                                    product['specifications'][key] = value
                break

        return product

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """Scrape single product"""
        delay = self.delay * random.uniform(0.8, 1.2)
        time.sleep(max(0.3, delay))

        soup = self.get_page(url)
        if soup:
            return self.extract_product_data(soup, url)
        return None

    def scrape_products(self, product_urls: List[str]) -> List[Dict]:
        """Scrape products concurrently"""
        products = []
        failed_urls = []

        self.stats['total'] = len(product_urls)
        self.stats['start_time'] = time.time()

        print(f"{'='*70}")
        print(f"SCRAPING {len(product_urls):,} PRODUCTS")
        print(f"{'='*70}")
        print(f"Workers: {self.workers}")
        print(f"Proxies: {len(self.proxy_manager.working_proxies) if self.proxy_manager else 0}")
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

                # Save every 1000
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
        print(f"\n  💾 Saved: {json_file} ({len(products):,} products)")

        # CSV
        csv_file = self.output_dir / f"products{suffix}_{timestamp}.csv"
        if products:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                flattened = []
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
                    flattened.append(flat)

                if flattened:
                    writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened)

    def print_summary(self):
        """Print summary"""
        elapsed = self.stats['end_time'] - self.stats['start_time']

        print(f"\n{'='*70}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'='*70}")
        print(f"Total: {self.stats['total']:,}")
        print(f"Success: {self.stats['success']:,} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"Failed: {self.stats['failed']:,} ({self.stats['failed']/self.stats['total']*100:.1f}%)")
        print(f"Time: {elapsed/60:.1f} minutes ({elapsed/3600:.2f} hours)")
        print(f"Rate: {self.stats['success']/elapsed:.2f} products/second")
        print(f"Output: {self.output_dir.absolute()}")
        print(f"{'='*70}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sitemap-based scraper with Crawl4AI approach')
    parser.add_argument('--webshare-api-key', type=str, required=True, help='Webshare API key')
    parser.add_argument('--workers', type=int, default=10, help='Workers (default: 10)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay (default: 0.5s)')
    parser.add_argument('--sitemap-start', type=int, default=1, help='Start sitemap number (default: 1)')
    parser.add_argument('--sitemap-end', type=int, default=151, help='End sitemap number (default: 151)')
    parser.add_argument('--max-products', type=int, help='Limit products (for testing)')
    parser.add_argument('--local-sitemaps', type=str, help='Path to local sitemap directory')
    parser.add_argument('--output-dir', type=str, default='sitemap_scraped_data', help='Output directory')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"SITEMAP-BASED SCRAPER WITH CRAWL4AI APPROACH")
    print(f"{'='*70}")
    print(f"Sitemaps: {args.sitemap_start}-{args.sitemap_end}")
    print(f"Workers: {args.workers}")
    print(f"Delay: {args.delay}s")
    print(f"{'='*70}\n")

    # Initialize scraper
    scraper = SitemapScraper(
        output_dir=args.output_dir,
        workers=args.workers,
        delay=args.delay
    )

    # Setup proxies
    scraper.proxy_manager = WebshareProxyManager(args.webshare_api_key)

    if not scraper.proxy_manager.fetch_proxies():
        print("❌ Failed to fetch proxies. Exiting.")
        return

    if not scraper.proxy_manager.validate_proxies():
        print("❌ No working proxies. Exiting.")
        return

    # Collect URLs from sitemaps
    product_urls = scraper.collect_urls_from_sitemaps(
        sitemap_range=(args.sitemap_start, args.sitemap_end),
        local_dir=args.local_sitemaps
    )

    if not product_urls:
        print("❌ No URLs found!")
        return

    # Limit for testing
    if args.max_products:
        product_urls = product_urls[:args.max_products]
        print(f"Limited to {len(product_urls):,} products for testing\n")

    # Scrape products
    products = scraper.scrape_products(product_urls)

    # Save final
    scraper.save_products(products, suffix="_final")

    # Summary
    scraper.print_summary()

    print("✅ Complete!")


if __name__ == '__main__':
    main()
