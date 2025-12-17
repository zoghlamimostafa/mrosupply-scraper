#!/usr/bin/env python3
"""
Production Scraper for mrosupply.com
Optimized for: 4 cores, 16GB RAM, 8 proxies
Target: 1,508,692 products
"""

import json
import csv
import time
import random
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from bs4 import BeautifulSoup

# Your 8 working proxies
WORKING_PROXIES = [
    "142.111.48.253:7030:yopfgyku:pn4xri0h48sy",
    "31.59.20.176:6754:yopfgyku:pn4xri0h48sy",
    "23.95.150.145:6114:yopfgyku:pn4xri0h48sy",
    "198.105.121.200:6462:yopfgyku:pn4xri0h48sy",
    "64.137.96.74:6641:yopfgyku:pn4xri0h48sy",
    "84.247.60.125:6095:yopfgyku:pn4xri0h48sy",
    "216.10.27.159:6837:yopfgyku:pn4xri0h48sy",
    "142.111.67.146:5611:yopfgyku:pn4xri0h48sy"
]

class ProductionScraper:
    def __init__(self, output_dir="production_data", workers=12, delay=0.8):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.delay = delay

        # Parse proxies
        self.proxies = []
        for proxy_str in WORKING_PROXIES:
            parts = proxy_str.split(':')
            ip, port, username, password = parts[0], parts[1], parts[2], parts[3]
            proxy_url = f"http://{username}:{password}@{ip}:{port}"
            self.proxies.append({
                'http': proxy_url,
                'https': proxy_url,
                'ip': ip
            })

        self.proxy_index = 0
        self.proxy_lock = Lock()

        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'start_time': None,
            'urls_collected': 0,
            'products_scraped': 0
        }
        self.stats_lock = Lock()

        # Data storage
        self.products = []
        self.failed_urls = []
        self.products_lock = Lock()

        print(f"="*70)
        print(f"PRODUCTION SCRAPER INITIALIZED")
        print(f"="*70)
        print(f"Configuration:")
        print(f"  Workers: {self.workers}")
        print(f"  Delay: {self.delay}s between requests")
        print(f"  Proxies: {len(self.proxies)} working proxies")
        print(f"  Output: {self.output_dir}/")
        print(f"="*70)

    def get_next_proxy(self):
        """Get next proxy in rotation"""
        with self.proxy_lock:
            proxy = self.proxies[self.proxy_index % len(self.proxies)]
            self.proxy_index += 1
            return proxy

    def get_page(self, url, timeout=15):
        """Fetch page with proxy rotation"""
        proxy = self.get_next_proxy()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            response = requests.get(url, proxies=proxy, headers=headers, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            return None

    def collect_product_urls(self, max_products=None):
        """Collect all product URLs from site - improved version"""
        print(f"\nPhase 1: Collecting product URLs...")
        print(f"="*70)

        product_urls = set()

        # Try multiple approaches to find all products
        # Approach 1: Browse all pages without filters
        page = 1
        consecutive_empty = 0
        max_consecutive_empty = 5

        print(f"\nScanning all product pages...")

        while True:
            if max_products and len(product_urls) >= max_products:
                break

            try:
                # Try both /search and /products endpoints
                new_products = 0

                for base_path in ['/search', '/products', '/shop', '/catalog']:
                    full_url = f"{self.base_url}{base_path}?page={page}"

                    soup = self.get_page(full_url)
                    if not soup:
                        continue

                    # Find product links - more comprehensive patterns
                    links = soup.find_all('a', href=True)

                    for link in links:
                        href = link['href']

                        # Match product URLs with various patterns
                        # Look for product detail pages, not just category pages
                        is_product = False

                        # Pattern 1: Category-based URLs
                        if any(cat in href for cat in [
                            '/hydraulics-', '/electrical-', '/mechanical-', '/tools-',
                            '/cleaning-', '/material-', '/safety-', '/welding-',
                            '/adhesives-', '/abrasives-', '/cutting-', '/fasteners-',
                            '/lubricants-', '/power-', '/pneumatic-', '/plumbing-'
                        ]):
                            is_product = True

                        # Pattern 2: /product/ or /p/ URLs
                        if '/product/' in href or '/p/' in href or '/item/' in href:
                            is_product = True

                        # Pattern 3: Product ID patterns
                        if '-p-' in href or '-sku-' in href:
                            is_product = True

                        # Exclude category listing pages
                        if '/category/' in href or '/categories/' in href:
                            is_product = False
                        if href.endswith('/') and href.count('/') <= 4:
                            is_product = False

                        if is_product:
                            if href.startswith('/'):
                                href = self.base_url + href
                            elif not href.startswith('http'):
                                continue

                            if href not in product_urls and self.base_url in href:
                                product_urls.add(href)
                                new_products += 1

                    time.sleep(self.delay / 2)  # Small delay between different paths

                if new_products > 0:
                    consecutive_empty = 0
                    print(f"  Page {page}: +{new_products} products (Total: {len(product_urls):,})")

                if new_products == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= max_consecutive_empty:
                        print(f"  Page {page}: No new products for {max_consecutive_empty} pages, stopping")
                        break
                    else:
                        print(f"  Page {page}: No new products ({consecutive_empty}/{max_consecutive_empty})")

                page += 1
                time.sleep(self.delay)

            except KeyboardInterrupt:
                print(f"\n\nInterrupted by user. Saving progress...")
                break
            except Exception as e:
                print(f"  Page {page}: Error - {str(e)[:50]}")
                time.sleep(2)
                continue

        # Approach 2: Try sitemap if available
        print(f"\nChecking for sitemap...")
        try:
            for sitemap_url in [
                f"{self.base_url}/sitemap.xml",
                f"{self.base_url}/sitemap_products.xml",
                f"{self.base_url}/product-sitemap.xml"
            ]:
                soup = self.get_page(sitemap_url)
                if soup:
                    # Parse sitemap XML
                    locs = soup.find_all('loc')
                    sitemap_products = 0
                    for loc in locs:
                        url = loc.get_text(strip=True)
                        # Only add if it looks like a product page
                        if any(pattern in url for pattern in ['/product/', '/p/', '-p-', '/item/']):
                            if url not in product_urls:
                                product_urls.add(url)
                                sitemap_products += 1

                    if sitemap_products > 0:
                        print(f"  Found {sitemap_products:,} additional products from sitemap")
                        break
                time.sleep(1)
        except Exception as e:
            print(f"  Sitemap not available or error: {str(e)[:50]}")

        self.stats['urls_collected'] = len(product_urls)

        print(f"\n{'='*70}")
        print(f"URL Collection Complete!")
        print(f"Total product URLs found: {len(product_urls):,}")
        print(f"{'='*70}\n")

        return list(product_urls)

    def scrape_product(self, url):
        """Scrape a single product"""
        try:
            soup = self.get_page(url)
            if not soup:
                return None

            # Extract product data
            product = {'url': url}

            # Name
            name = soup.find('h1')
            product['name'] = name.get_text(strip=True) if name else None

            # Price
            price = soup.find('span', class_='price')
            if not price:
                price = soup.find('div', {'class': 'price'})
            product['price'] = price.get_text(strip=True) if price else None

            # Brand
            brand = soup.find('span', {'itemprop': 'brand'})
            if not brand:
                brand = soup.find('a', {'class': 'brand'})
            product['brand'] = brand.get_text(strip=True) if brand else None

            # MPN
            mpn = soup.find('span', {'itemprop': 'mpn'})
            product['mpn'] = mpn.get_text(strip=True) if mpn else None

            # SKU
            sku = soup.find('span', {'itemprop': 'sku'})
            product['sku'] = sku.get_text(strip=True) if sku else None

            # Category
            breadcrumb = soup.find('nav', {'aria-label': 'breadcrumb'})
            if breadcrumb:
                links = breadcrumb.find_all('a')
                product['category'] = ' > '.join([l.get_text(strip=True) for l in links])
            else:
                product['category'] = None

            # Images
            images = []
            img_tags = soup.find_all('img', {'class': 'product-image'})
            for img in img_tags:
                if 'src' in img.attrs:
                    images.append(img['src'])
            product['images'] = images

            # Availability
            availability = soup.find('span', {'itemprop': 'availability'})
            product['availability'] = availability.get_text(strip=True) if availability else None

            # Specifications
            specs = {}
            spec_table = soup.find('table', {'class': 'specifications'})
            if spec_table:
                rows = spec_table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True)
                        value = cols[1].get_text(strip=True)
                        specs[key] = value
            product['specifications'] = specs

            return product

        except Exception as e:
            return None

    def scrape_products(self, urls):
        """Scrape all products with progress tracking"""
        print(f"\nPhase 2: Scraping Products")
        print(f"="*70)
        print(f"Total products: {len(urls):,}")
        print(f"Workers: {self.workers}")
        print(f"Estimated time: {len(urls) * self.delay / self.workers / 60:.1f} minutes")
        print(f"="*70)

        self.stats['start_time'] = time.time()
        self.stats['total'] = len(urls)

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.scrape_product, url): url for url in urls}

            for future in as_completed(futures):
                url = futures[future]

                try:
                    product = future.result()

                    if product and product.get('name'):
                        with self.products_lock:
                            self.products.append(product)
                        with self.stats_lock:
                            self.stats['success'] += 1
                    else:
                        with self.products_lock:
                            self.failed_urls.append(url)
                        with self.stats_lock:
                            self.stats['failed'] += 1

                    # Progress update
                    with self.stats_lock:
                        completed = self.stats['success'] + self.stats['failed']
                        success_rate = (self.stats['success'] / completed * 100) if completed > 0 else 0
                        elapsed = time.time() - self.stats['start_time']
                        speed = completed / elapsed if elapsed > 0 else 0
                        remaining = (self.stats['total'] - completed) / speed if speed > 0 else 0

                        if completed % 50 == 0 or completed == self.stats['total']:
                            print(f"Progress: {completed}/{self.stats['total']} ({completed/self.stats['total']*100:.1f}%) | "
                                  f"Success: {self.stats['success']} ({success_rate:.1f}%) | "
                                  f"Speed: {speed:.2f}/s | "
                                  f"ETA: {remaining/60:.1f}m")

                        # Incremental save every 500 products
                        if self.stats['success'] > 0 and self.stats['success'] % 500 == 0:
                            self.save_progress()

                except Exception as e:
                    with self.stats_lock:
                        self.stats['failed'] += 1
                    with self.products_lock:
                        self.failed_urls.append(url)

                # Delay between requests
                time.sleep(self.delay)

        self.stats['end_time'] = time.time()

    def save_progress(self):
        """Save current progress"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save products
        if self.products:
            json_file = self.output_dir / f"products_progress_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(self.products, f, indent=2)
            print(f"\n  💾 Progress saved: {len(self.products)} products -> {json_file.name}")

    def save_final_results(self):
        """Save final results"""
        print(f"\n{'='*70}")
        print(f"SAVING FINAL RESULTS")
        print(f"{'='*70}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save products as JSON
        if self.products:
            json_file = self.output_dir / f"products_final_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(self.products, f, indent=2)
            print(f"✅ Saved JSON: {json_file}")
            print(f"   Products: {len(self.products):,}")

            # Save as CSV
            csv_file = self.output_dir / f"products_final_{timestamp}.csv"
            if self.products:
                keys = self.products[0].keys()
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    for product in self.products:
                        # Convert lists/dicts to strings for CSV
                        row = {}
                        for k, v in product.items():
                            if isinstance(v, (list, dict)):
                                row[k] = json.dumps(v)
                            else:
                                row[k] = v
                        writer.writerow(row)
                print(f"✅ Saved CSV: {csv_file}")

        # Save failed URLs
        if self.failed_urls:
            failed_file = self.output_dir / f"failed_urls_{timestamp}.txt"
            with open(failed_file, 'w') as f:
                for url in self.failed_urls:
                    f.write(url + '\n')
            print(f"⚠️  Failed URLs: {failed_file}")
            print(f"   Count: {len(self.failed_urls):,}")

        # Save statistics
        stats_file = self.output_dir / f"statistics_{timestamp}.json"
        total_time = self.stats['end_time'] - self.stats['start_time']
        stats_summary = {
            'total_products': self.stats['total'],
            'successful': self.stats['success'],
            'failed': self.stats['failed'],
            'success_rate': (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0,
            'total_time_seconds': total_time,
            'total_time_hours': total_time / 3600,
            'average_speed': self.stats['success'] / total_time if total_time > 0 else 0,
            'start_time': datetime.fromtimestamp(self.stats['start_time']).isoformat(),
            'end_time': datetime.fromtimestamp(self.stats['end_time']).isoformat(),
        }
        with open(stats_file, 'w') as f:
            json.dump(stats_summary, f, indent=2)
        print(f"📊 Statistics: {stats_file}")

        print(f"{'='*70}\n")

    def print_final_summary(self):
        """Print final summary"""
        total_time = self.stats['end_time'] - self.stats['start_time']

        print(f"\n{'='*70}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'='*70}")
        print(f"Total products targeted: {self.stats['total']:,}")
        print(f"Successfully scraped:    {self.stats['success']:,} ({self.stats['success']/self.stats['total']*100:.1f}%)")
        print(f"Failed:                  {self.stats['failed']:,} ({self.stats['failed']/self.stats['total']*100:.1f}%)")
        print(f"Total time:              {total_time/60:.1f} minutes ({total_time/3600:.2f} hours)")
        print(f"Average speed:           {self.stats['success']/total_time:.2f} products/second")
        print(f"Output directory:        {self.output_dir.absolute()}")
        print(f"{'='*70}\n")

    def run(self, max_products=None):
        """Run the complete scraping process"""
        try:
            # Step 1: Collect URLs
            urls = self.collect_product_urls(max_products=max_products)

            if not urls:
                print("❌ No product URLs found!")
                return

            # Step 2: Scrape products
            self.scrape_products(urls)

            # Step 3: Save results
            self.save_final_results()

            # Step 4: Print summary
            self.print_final_summary()

            return True

        except KeyboardInterrupt:
            print(f"\n\n{'='*70}")
            print(f"INTERRUPTED BY USER")
            print(f"{'='*70}")
            self.stats['end_time'] = time.time()
            self.save_final_results()
            self.print_final_summary()
            return False
        except Exception as e:
            print(f"\n\n{'='*70}")
            print(f"ERROR OCCURRED")
            print(f"{'='*70}")
            print(f"Error: {str(e)}")
            self.stats['end_time'] = time.time()
            self.save_final_results()
            return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   MROSUPPLY.COM PRODUCTION SCRAPER                   ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Configuration
    WORKERS = 12          # Optimized for 4-core server (3 per core)
    DELAY = 0.8          # 0.8 seconds = ~1.5 products/second with 12 workers
    OUTPUT_DIR = "production_data"

    # Optional: limit products for testing
    MAX_PRODUCTS = None  # Set to None for all products, or number for testing

    print(f"Server specs: 4 cores, 16GB RAM")
    print(f"Configuration: {WORKERS} workers, {DELAY}s delay")
    print(f"Target: All products (estimated 1.5M)")
    print(f"\nStarting in 5 seconds... (Ctrl+C to cancel)\n")

    try:
        for i in range(5, 0, -1):
            print(f"  Starting in {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\nCancelled by user.\n")
        return

    # Create and run scraper
    scraper = ProductionScraper(
        output_dir=OUTPUT_DIR,
        workers=WORKERS,
        delay=DELAY
    )

    success = scraper.run(max_products=MAX_PRODUCTS)

    if success:
        print(f"✅ Scraping completed successfully!")
    else:
        print(f"⚠️  Scraping ended early (interrupted or error)")

    print(f"\nResults saved to: {OUTPUT_DIR}/")
    print(f"\nTo resume or retry failed URLs, check failed_urls_*.txt")

if __name__ == '__main__':
    main()
