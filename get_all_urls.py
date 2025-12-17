#!/usr/bin/env python3
"""
Extract ALL 1.5M Product URLs from Sitemap XMLs (1-151)
Saves to a single file for later use
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List
import requests
import time
from datetime import datetime


class SitemapURLExtractor:
    """Extract all URLs from sitemap XMLs"""

    def __init__(self, base_url: str = "https://www.mrosupply.com"):
        self.base_url = base_url
        self.all_urls = []

    def parse_local_sitemap(self, sitemap_file: str) -> List[str]:
        """Parse a local sitemap XML file"""
        urls = []

        try:
            tree = ET.parse(sitemap_file)
            root = tree.getroot()

            # Handle XML namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url_elem in root.findall('ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    urls.append(loc.text)

        except Exception as e:
            print(f"    ❌ Error: {e}")

        return urls

    def download_sitemap(self, sitemap_num: int) -> List[str]:
        """Download and parse sitemap from web"""
        sitemap_url = f"{self.base_url}/sitemap-product-{sitemap_num}.xml"
        urls = []

        try:
            response = requests.get(sitemap_url, timeout=15)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Handle XML namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url_elem in root.findall('ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is not None and loc.text:
                    urls.append(loc.text)

        except Exception as e:
            print(f"    ❌ Error: {e}")

        return urls

    def extract_all_urls(self, sitemap_range: tuple = (1, 151), local_dir: str = None) -> List[str]:
        """Extract all URLs from sitemaps 1-151"""
        print(f"\n{'='*70}")
        print(f"EXTRACTING ALL PRODUCT URLS FROM SITEMAPS {sitemap_range[0]}-{sitemap_range[1]}")
        print(f"{'='*70}\n")

        start_time = time.time()

        for sitemap_num in range(sitemap_range[0], sitemap_range[1] + 1):
            print(f"[{sitemap_num}/{sitemap_range[1]}] Processing sitemap-product-{sitemap_num}.xml...", end=' ')

            urls = []

            # Try local file first
            if local_dir:
                local_file = Path(local_dir) / f"sitemap-product-{sitemap_num}.xml"
                if local_file.exists():
                    print(f"(local)", end=' ')
                    urls = self.parse_local_sitemap(str(local_file))
                    if urls:
                        print(f"✅ {len(urls):,} URLs")
                        self.all_urls.extend(urls)
                        continue

            # Download from web if local not available
            print(f"(downloading)", end=' ')
            urls = self.download_sitemap(sitemap_num)
            if urls:
                print(f"✅ {len(urls):,} URLs")
                self.all_urls.extend(urls)
            else:
                print(f"❌ Failed")

            time.sleep(0.3)  # Be polite to the server

        # Remove duplicates
        original_count = len(self.all_urls)
        self.all_urls = list(set(self.all_urls))
        duplicates = original_count - len(self.all_urls)

        elapsed = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"EXTRACTION COMPLETE!")
        print(f"{'='*70}")
        print(f"Total URLs extracted: {original_count:,}")
        print(f"Duplicates removed: {duplicates:,}")
        print(f"Unique URLs: {len(self.all_urls):,}")
        print(f"Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"{'='*70}\n")

        return self.all_urls

    def save_urls(self, output_file: str = "all_product_urls.txt", format: str = "txt", sitemap_range: tuple = (1, 151)):
        """Save URLs to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "txt":
            # Save as text file (one URL per line)
            filename = f"all_product_urls_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for url in self.all_urls:
                    f.write(url + '\n')
            print(f"✅ Saved as TXT: {filename}")
            print(f"   {len(self.all_urls):,} URLs")

        elif format == "json":
            # Save as JSON
            filename = f"all_product_urls_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_urls, f, indent=2)
            print(f"✅ Saved as JSON: {filename}")
            print(f"   {len(self.all_urls):,} URLs")

        elif format == "both":
            # Save both formats
            txt_filename = f"all_product_urls_{timestamp}.txt"
            with open(txt_filename, 'w', encoding='utf-8') as f:
                for url in self.all_urls:
                    f.write(url + '\n')
            print(f"✅ Saved as TXT: {txt_filename}")

            json_filename = f"all_product_urls_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_urls, f, indent=2)
            print(f"✅ Saved as JSON: {json_filename}")

            print(f"   {len(self.all_urls):,} URLs in both files")
            filename = txt_filename  # Use txt filename as the primary return value

        # Also save summary
        summary_file = f"url_extraction_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("URL EXTRACTION SUMMARY\n")
            f.write("="*70 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total URLs: {len(self.all_urls):,}\n")
            f.write(f"Sitemaps processed: {sitemap_range[0]}-{sitemap_range[1]}\n")
            f.write(f"\nSample URLs (first 10):\n")
            for i, url in enumerate(self.all_urls[:10], 1):
                f.write(f"  {i}. {url}\n")
            f.write("="*70 + "\n")
        print(f"✅ Saved summary: {summary_file}\n")

        return filename


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Extract all 1.5M product URLs from sitemaps')
    parser.add_argument('--sitemap-start', type=int, default=1, help='Start sitemap number (default: 1)')
    parser.add_argument('--sitemap-end', type=int, default=151, help='End sitemap number (default: 151)')
    parser.add_argument('--local-sitemaps', type=str, help='Path to local sitemap directory')
    parser.add_argument('--format', choices=['txt', 'json', 'both'], default='both',
                        help='Output format (default: both)')
    parser.add_argument('--output', type=str, help='Custom output filename (without extension)')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"ALL PRODUCT URL EXTRACTOR")
    print(f"{'='*70}")
    print(f"Target: Extract ALL product URLs from sitemaps {args.sitemap_start}-{args.sitemap_end}")
    print(f"Format: {args.format}")
    if args.local_sitemaps:
        print(f"Local sitemaps: {args.local_sitemaps}")
    else:
        print(f"Source: Download from web")
    print(f"{'='*70}\n")

    # Create extractor
    extractor = SitemapURLExtractor()

    # Extract all URLs
    urls = extractor.extract_all_urls(
        sitemap_range=(args.sitemap_start, args.sitemap_end),
        local_dir=args.local_sitemaps
    )

    if not urls:
        print("❌ No URLs extracted!")
        return

    # Save URLs
    extractor.save_urls(
        output_file=args.output if args.output else "all_product_urls.txt",
        format=args.format,
        sitemap_range=(args.sitemap_start, args.sitemap_end)
    )

    print(f"\n{'='*70}")
    print(f"NEXT STEPS")
    print(f"{'='*70}")
    print(f"You now have {len(urls):,} product URLs!")
    print(f"\nTo scrape these products, use:")
    print(f"  python3 scrape_from_url_file.py --url-file all_product_urls_*.txt")
    print(f"{'='*70}\n")

    print("✅ Complete!")


if __name__ == '__main__':
    main()
