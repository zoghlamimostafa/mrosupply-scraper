#!/usr/bin/env python3
"""
Tor-Enabled Scraper for mrosupply.com
Uses Tor as FREE proxy alternative
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
import socket


class TorProxyManager:
    """Manage Tor SOCKS5 proxies"""

    def __init__(self, tor_ports: List[int] = None):
        """
        Initialize Tor proxy manager

        Args:
            tor_ports: List of Tor SOCKS ports (default: [9050])
        """
        self.tor_ports = tor_ports or [9050]
        self.current_index = 0
        self.proxy_lock = Lock()
        self.proxy_stats = {}

        for port in self.tor_ports:
            self.proxy_stats[port] = {'success': 0, 'failed': 0}

    def test_tor_connection(self, port: int = 9050) -> bool:
        """Test if Tor is running on specified port"""
        try:
            proxies = {
                'http': f'socks5://127.0.0.1:{port}',
                'https': f'socks5://127.0.0.1:{port}'
            }
            response = requests.get(
                'https://check.torproject.org/api/ip',
                proxies=proxies,
                timeout=10
            )
            data = response.json()
            is_tor = data.get('IsTor', False)

            if is_tor:
                print(f"  ✅ Tor on port {port}: Working (IP: {data.get('IP')})")
            else:
                print(f"  ❌ Tor on port {port}: Not using Tor (IP: {data.get('IP')})")

            return is_tor
        except Exception as e:
            print(f"  ❌ Tor on port {port}: Error - {str(e)[:50]}")
            return False

    def validate_all_tor_instances(self) -> List[int]:
        """Test all Tor instances and return working ports"""
        print(f"\n{'='*70}")
        print(f"VALIDATING TOR INSTANCES")
        print(f"{'='*70}")

        working_ports = []

        for port in self.tor_ports:
            if self.test_tor_connection(port):
                working_ports.append(port)

        print(f"\n{'='*70}")
        print(f"Working Tor instances: {len(working_ports)}/{len(self.tor_ports)}")
        print(f"{'='*70}\n")

        self.tor_ports = working_ports
        return working_ports

    def get_next_proxy(self) -> Optional[dict]:
        """Get next Tor proxy in rotation"""
        if not self.tor_ports:
            return None

        with self.proxy_lock:
            port = self.tor_ports[self.current_index % len(self.tor_ports)]
            self.current_index += 1

            return {
                'http': f'socks5://127.0.0.1:{port}',
                'https': f'socks5://127.0.0.1:{port}',
                'port': port
            }

    def mark_success(self, proxy: dict):
        """Mark proxy as successful"""
        if proxy and proxy['port'] in self.proxy_stats:
            self.proxy_stats[proxy['port']]['success'] += 1

    def mark_failed(self, proxy: dict):
        """Mark proxy as failed"""
        if proxy and proxy['port'] in self.proxy_stats:
            self.proxy_stats[proxy['port']]['failed'] += 1

    def print_stats(self):
        """Print Tor proxy statistics"""
        print(f"\n{'='*70}")
        print(f"TOR PROXY STATISTICS")
        print(f"{'='*70}")

        total_success = 0
        total_failed = 0

        for port, stats in self.proxy_stats.items():
            success = stats['success']
            failed = stats['failed']
            total = success + failed
            success_rate = (success / total * 100) if total > 0 else 0

            total_success += success
            total_failed += failed

            print(f"  Port {port}:")
            print(f"    Success: {success} | Failed: {failed} | Rate: {success_rate:.1f}%")

        overall_total = total_success + total_failed
        overall_rate = (total_success / overall_total * 100) if overall_total > 0 else 0

        print(f"\n  Overall:")
        print(f"    Total requests: {overall_total}")
        print(f"    Success: {total_success} ({overall_rate:.1f}%)")
        print(f"    Failed: {total_failed} ({100-overall_rate:.1f}%)")
        print(f"{'='*70}\n")


class TorScraper:
    """Sitemap scraper with Tor proxy support"""

    def __init__(self, output_dir: str = "tor_scraped_data", workers: int = 10,
                 delay: float = 1.0, use_tor: bool = True, tor_ports: List[int] = None):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.delay = delay
        self.use_tor = use_tor
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

        # Tor manager
        self.tor_manager = None
        if use_tor:
            self.tor_manager = TorProxyManager(tor_ports=tor_ports)

        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def download_sitemap(self, sitemap_num: int) -> List[str]:
        """Download and parse sitemap"""
        sitemap_url = f"{self.base_url}/sitemap-product-{sitemap_num}.xml"
        urls = []

        try:
            response = requests.get(sitemap_url, timeout=15)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url_elem in root.findall('ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    urls.append(loc.text)

        except Exception as e:
            print(f"  ❌ Error downloading sitemap {sitemap_num}: {e}")

        return urls

    def collect_urls_from_sitemaps(self, sitemap_range: tuple = (1, 151)) -> List[str]:
        """Collect URLs from sitemaps"""
        print(f"\n{'='*70}")
        print(f"COLLECTING URLS FROM SITEMAPS {sitemap_range[0]}-{sitemap_range[1]}")
        print(f"{'='*70}\n")

        all_urls = []

        for sitemap_num in range(sitemap_range[0], sitemap_range[1] + 1):
            print(f"[{sitemap_num}/{sitemap_range[1]}] Downloading sitemap-product-{sitemap_num}.xml...", end=' ')

            urls = self.download_sitemap(sitemap_num)
            if urls:
                all_urls.extend(urls)
                print(f"✅ {len(urls):,} URLs")
            else:
                print(f"❌ Failed")

            time.sleep(0.5)

        all_urls = list(set(all_urls))

        print(f"\n{'='*70}")
        print(f"Total unique URLs: {len(all_urls):,}")
        print(f"{'='*70}\n")

        return all_urls

    def get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch page with Tor proxy"""
        for attempt in range(max_retries):
            proxy = None
            try:
                if self.use_tor and self.tor_manager:
                    proxy = self.tor_manager.get_next_proxy()

                if proxy:
                    response = self.session.get(url, proxies=proxy, timeout=20)
                else:
                    response = self.session.get(url, timeout=15)

                response.raise_for_status()

                if proxy:
                    self.tor_manager.mark_success(proxy)

                return BeautifulSoup(response.text, 'html.parser')

            except Exception:
                if proxy:
                    self.tor_manager.mark_failed(proxy)

                if attempt < max_retries - 1:
                    time.sleep(1)

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

                    offers = data.get('offers', [])
                    if isinstance(offers, list) and offers:
                        offer = offers[0]
                        product['sku'] = str(offer.get('sku', ''))
                        product['mpn'] = offer.get('mpn', '')
                        product['price'] = f"${offer.get('price', '')}"
            except:
                pass

        return product

    def scrape_single_product(self, url: str) -> Optional[Dict]:
        """Scrape single product"""
        delay = self.delay * random.uniform(0.8, 1.2)
        time.sleep(max(0.5, delay))

        soup = self.get_page(url)
        if soup:
            return self.extract_product_data(soup, url)
        return None

    def scrape_products(self, product_urls: List[str]) -> List[Dict]:
        """Scrape products"""
        products = []
        failed_urls = []

        self.stats['total'] = len(product_urls)
        self.stats['start_time'] = time.time()

        print(f"{'='*70}")
        print(f"SCRAPING {len(product_urls):,} PRODUCTS")
        print(f"{'='*70}")
        print(f"Workers: {self.workers}")
        print(f"Using Tor: {'YES' if self.use_tor else 'NO'}")
        if self.use_tor:
            print(f"Tor instances: {len(self.tor_manager.tor_ports)}")
        print(f"Delay: {self.delay}s")
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

                completed = self.stats['success'] + self.stats['failed']
                if completed % 100 == 0 or completed == len(product_urls):
                    elapsed = time.time() - self.stats['start_time']
                    rate = completed / elapsed if elapsed > 0 else 0
                    print(f"Progress: {completed:,}/{len(product_urls):,} | "
                          f"Success: {self.stats['success']:,} | Rate: {rate:.2f}/s")

                if self.stats['success'] % 1000 == 0 and self.stats['success'] > 0:
                    self.save_products(products, suffix=f"_progress_{self.stats['success']}")

        self.stats['end_time'] = time.time()

        if failed_urls:
            failed_file = self.output_dir / "failed_urls.txt"
            with open(failed_file, 'w') as f:
                f.write('\n'.join(failed_urls))

        return products

    def save_products(self, products: List[Dict], suffix: str = ""):
        """Save products"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_file = self.output_dir / f"products{suffix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Saved: {len(products):,} products")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Tor-enabled scraper')
    parser.add_argument('--workers', type=int, default=10, help='Workers (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay (default: 1.0s)')
    parser.add_argument('--sitemap-start', type=int, default=1, help='Start sitemap')
    parser.add_argument('--sitemap-end', type=int, default=151, help='End sitemap')
    parser.add_argument('--max-products', type=int, help='Limit products')
    parser.add_argument('--tor-ports', type=str, default='9050', help='Tor ports (comma-separated)')
    parser.add_argument('--no-tor', action='store_true', help='Disable Tor (direct connection)')
    parser.add_argument('--output-dir', type=str, default='tor_scraped_data', help='Output directory')

    args = parser.parse_args()

    # Parse Tor ports
    tor_ports = [int(p.strip()) for p in args.tor_ports.split(',')]

    print(f"\n{'='*70}")
    print(f"TOR-ENABLED SCRAPER")
    print(f"{'='*70}")
    print(f"Sitemaps: {args.sitemap_start}-{args.sitemap_end}")
    print(f"Workers: {args.workers}")
    print(f"Using Tor: {'NO' if args.no_tor else 'YES'}")
    if not args.no_tor:
        print(f"Tor ports: {', '.join(map(str, tor_ports))}")
    print(f"{'='*70}\n")

    # Initialize scraper
    scraper = TorScraper(
        output_dir=args.output_dir,
        workers=args.workers,
        delay=args.delay,
        use_tor=not args.no_tor,
        tor_ports=tor_ports
    )

    # Validate Tor if enabled
    if not args.no_tor:
        working_ports = scraper.tor_manager.validate_all_tor_instances()
        if not working_ports:
            print("❌ No working Tor instances! Run without --no-tor or check Tor installation.")
            return

    # Collect URLs
    urls = scraper.collect_urls_from_sitemaps(
        sitemap_range=(args.sitemap_start, args.sitemap_end)
    )

    if args.max_products:
        urls = urls[:args.max_products]

    # Scrape
    products = scraper.scrape_products(urls)
    scraper.save_products(products, suffix="_final")

    # Stats
    if scraper.tor_manager:
        scraper.tor_manager.print_stats()

    print("✅ Complete!")


if __name__ == '__main__':
    main()
