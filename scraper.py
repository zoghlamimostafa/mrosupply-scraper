#!/usr/bin/env python3
"""
MROSupply.com Product Scraper
Scrapes product information including details, images, specifications, descriptions, and documents
"""

import json
import csv
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


class MROSupplyScraper:
    """Scraper for MROSupply.com products"""

    def __init__(self, output_dir: str = "scraped_data"):
        self.base_url = "https://www.mrosupply.com"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"Failed to fetch {url} after {max_retries} attempts")
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

        # Extract from JSON-LD structured data (most reliable)
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if data.get('@type') == 'Product':
                    product_data['name'] = data.get('name', '')
                    product_data['description'] = data.get('description', '')
                    product_data['category'] = data.get('category', '')

                    # Extract image
                    if data.get('image'):
                        product_data['images'].append(data['image'])

                    # Extract offer data
                    offers = data.get('offers', [])
                    if isinstance(offers, list) and offers:
                        offer = offers[0]
                        product_data['sku'] = str(offer.get('sku', ''))
                        product_data['mpn'] = offer.get('mpn', '')
                        product_data['price'] = f"${offer.get('price', '')}"
                        product_data['availability'] = offer.get('availability', '')
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON-LD: {e}")

        # Extract brand from meta tags
        brand_meta = soup.find('meta', property='og:brand') or soup.find('meta', {'name': 'twitter:data1'})
        if brand_meta:
            product_data['brand'] = brand_meta.get('content', brand_meta.get('value', ''))

        # Extract price from page (backup)
        price_elem = soup.find('p', class_='price')
        if price_elem and not product_data['price']:
            product_data['price'] = price_elem.get_text(strip=True)

        # Extract price note
        price_note = soup.find('p', class_='muted')
        if price_note and 'Prices are subject to change' in price_note.get_text():
            product_data['price_note'] = price_note.get_text(strip=True)

        # Extract additional images from gallery
        image_gallery = soup.find_all('img', {'data-zoom-image': True})
        for img in image_gallery:
            img_url = img.get('data-zoom-image') or img.get('src')
            if img_url and img_url not in product_data['images']:
                product_data['images'].append(img_url)

        # Extract specifications
        spec_sections = soup.find_all('div', class_='m-accordion--item')
        for spec_section in spec_sections:
            spec_head = spec_section.find('button', class_='m-accordion--item--head')
            if spec_head and 'SPECIFICATION' in spec_head.get_text():
                spec_body = spec_section.find('div', class_='m-accordion--item--body')
                if spec_body:
                    # Try to find o-grid-table (new structure)
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
                    else:
                        # Fallback to table structure (old structure)
                        spec_table = spec_body.find('table')
                        if spec_table:
                            for row in spec_table.find_all('tr'):
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    key = cells[0].get_text(strip=True)
                                    value = cells[1].get_text(strip=True)
                                    if key and value:
                                        product_data['specifications'][key] = value
                break

        # Extract additional description
        additional_desc_section = soup.find('div', id='additionalDescription')
        if additional_desc_section:
            desc_body = additional_desc_section.find('div', class_='m-accordion--item--body')
            if desc_body:
                # Get all text content, preserving structure
                desc_text = desc_body.get_text(separator='\n', strip=True)
                product_data['additional_description'] = desc_text

        # Extract documents/software
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

        # Extract related products
        related_section = soup.find_all('div', class_='m-catalogue-product')
        for product in related_section[:5]:  # Limit to first 5 related products
            product_link = product.find('a', class_='m-catalogue-product-title')
            if product_link:
                related_url = product_link.get('href', '')
                related_name = product_link.get_text(strip=True)
                related_price_elem = product.find('div', class_='m-catalogue-product-price')
                related_price = related_price_elem.get_text(strip=True) if related_price_elem else ''

                product_data['related_products'].append({
                    'name': related_name,
                    'url': urljoin(self.base_url, related_url),
                    'price': related_price
                })

        return product_data

    def get_sitemap_categories(self) -> List[str]:
        """Get all category URLs from the sitemap"""
        sitemap_url = f"{self.base_url}/cindex/"
        print(f"Fetching sitemap: {sitemap_url}")

        soup = self.get_page(sitemap_url)
        if not soup:
            return []

        category_urls = []
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href')
            # Look for category/product links
            if href and ('/' in href) and not any(skip in href for skip in ['javascript:', 'mailto:', '#']):
                full_url = urljoin(self.base_url, href)
                if self.base_url in full_url:
                    category_urls.append(full_url)

        # Remove duplicates
        category_urls = list(set(category_urls))
        print(f"Found {len(category_urls)} URLs from sitemap")
        return category_urls

    def get_product_urls_from_search(self, per_page: int = 120, max_pages: Optional[int] = None) -> List[str]:
        """Get all product URLs from search results"""
        product_urls = []
        page = 1

        while True:
            if max_pages and page > max_pages:
                break

            search_url = f"{self.base_url}/search/?q=&per_page={per_page}&page={page}"
            print(f"Fetching search page {page}: {search_url}")

            soup = self.get_page(search_url)
            if not soup:
                break

            # Find product links
            products = soup.find_all('a', class_='m-catalogue-product-title')
            if not products:
                print(f"No more products found on page {page}")
                break

            for product in products:
                href = product.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    product_urls.append(full_url)

            print(f"Found {len(products)} products on page {page}")
            page += 1
            time.sleep(1)  # Be polite

        # Remove duplicates
        product_urls = list(set(product_urls))
        print(f"Total unique products found: {len(product_urls)}")
        return product_urls

    def scrape_local_file(self, file_path: str) -> Dict:
        """Scrape a local HTML file"""
        print(f"Scraping local file: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # Try to get URL from meta tags or use file path
        canonical = soup.find('link', rel='canonical')
        url = canonical.get('href') if canonical else file_path

        return self.extract_product_data(soup, url)

    def scrape_products(self, product_urls: List[str], delay: float = 1.0) -> List[Dict]:
        """Scrape multiple products"""
        products = []
        total = len(product_urls)

        for i, url in enumerate(product_urls, 1):
            print(f"Scraping product {i}/{total}: {url}")

            soup = self.get_page(url)
            if soup:
                product_data = self.extract_product_data(soup, url)
                products.append(product_data)

                # Save incrementally
                if i % 10 == 0:
                    self.save_products(products, suffix=f"_batch_{i}")

            time.sleep(delay)  # Be polite to the server

        return products

    def save_products(self, products: List[Dict], suffix: str = "") -> None:
        """Save products to JSON and CSV files"""
        # Save as JSON
        json_file = self.output_dir / f"products{suffix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(products)} products to {json_file}")

        # Save as CSV (flatten the data)
        csv_file = self.output_dir / f"products{suffix}.csv"
        if products:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                # Flatten nested structures for CSV
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

                writer = csv.DictWriter(f, fieldnames=flattened_products[0].keys())
                writer.writeheader()
                writer.writerows(flattened_products)
            print(f"Saved {len(products)} products to {csv_file}")


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape products from MROSupply.com')
    parser.add_argument('--mode', choices=['search', 'sitemap', 'local', 'test'], default='search',
                      help='Scraping mode: search (search results), sitemap (from sitemap), local (local HTML file), test (test with example file)')
    parser.add_argument('--file', type=str, help='Path to local HTML file (for local mode)')
    parser.add_argument('--max-pages', type=int, help='Maximum number of search pages to scrape')
    parser.add_argument('--max-products', type=int, help='Maximum number of products to scrape')
    parser.add_argument('--output-dir', type=str, default='scraped_data', help='Output directory')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')

    args = parser.parse_args()

    scraper = MROSupplyScraper(output_dir=args.output_dir)

    if args.mode == 'local' or args.mode == 'test':
        # Scrape local file
        if args.mode == 'test':
            file_path = '755-702-413139 Rotary Union Deublin _ MROSupply.com - MROSupply.com.html'
        else:
            file_path = args.file

        if not file_path:
            print("Error: --file argument required for local mode")
            return

        product = scraper.scrape_local_file(file_path)
        scraper.save_products([product])

        # Print summary
        print("\n=== Product Summary ===")
        print(f"Name: {product['name']}")
        print(f"Brand: {product['brand']}")
        print(f"MPN: {product['mpn']}")
        print(f"Price: {product['price']}")
        print(f"Images: {len(product['images'])} found")
        print(f"Specifications: {len(product['specifications'])} found")
        print(f"Documents: {len(product['documents'])} found")

    elif args.mode == 'search':
        # Get products from search
        product_urls = scraper.get_product_urls_from_search(max_pages=args.max_pages)

        if args.max_products:
            product_urls = product_urls[:args.max_products]

        print(f"\nScraping {len(product_urls)} products...")
        products = scraper.scrape_products(product_urls, delay=args.delay)
        scraper.save_products(products)

    elif args.mode == 'sitemap':
        # Get URLs from sitemap
        urls = scraper.get_sitemap_categories()

        if args.max_products:
            urls = urls[:args.max_products]

        print(f"\nScraping {len(urls)} URLs...")
        products = scraper.scrape_products(urls, delay=args.delay)
        scraper.save_products(products)

    print("\n=== Scraping Complete ===")


if __name__ == '__main__':
    main()
