#!/usr/bin/env python3
"""
Batch Scraper for Large-Scale Scraping
Splits large jobs into manageable batches with resume capability
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from fast_scraper import FastMROSupplyScraper


class BatchScraper:
    """Batch scraper with resume capability"""

    def __init__(self, output_dir: str = "scraped_data", workers: int = 16):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.workers = workers
        self.state_file = self.output_dir / "batch_state.json"
        self.scraper = FastMROSupplyScraper(output_dir=str(self.output_dir), max_workers=workers)

    def save_state(self, state: dict):
        """Save batch processing state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> dict:
        """Load previous batch processing state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return None

    def scrape_in_batches(self, product_urls: list, batch_size: int = 250000):
        """Scrape products in batches with resume capability"""

        # Check for existing state
        state = self.load_state()
        start_batch = 0
        all_products = []

        if state:
            print(f"\n{'='*70}")
            print(f"FOUND PREVIOUS RUN")
            print(f"{'='*70}")
            print(f"Completed batches: {state['completed_batches']}/{state['total_batches']}")
            print(f"Products scraped: {state['total_scraped']:,}")
            print(f"Last run: {state['last_run']}")

            response = input(f"\nResume from batch {state['completed_batches'] + 1}? [Y/n]: ").lower()
            if response != 'n':
                start_batch = state['completed_batches']
                # Load previously scraped products
                for i in range(start_batch):
                    batch_file = self.output_dir / f"batch_{i+1}_products.json"
                    if batch_file.exists():
                        with open(batch_file, 'r') as f:
                            batch_products = json.load(f)
                            all_products.extend(batch_products)
                print(f"Loaded {len(all_products):,} previously scraped products")
            print(f"{'='*70}\n")

        # Split into batches
        total_batches = (len(product_urls) + batch_size - 1) // batch_size

        print(f"\n{'='*70}")
        print(f"BATCH PROCESSING CONFIGURATION")
        print(f"{'='*70}")
        print(f"Total products: {len(product_urls):,}")
        print(f"Batch size: {batch_size:,}")
        print(f"Total batches: {total_batches}")
        print(f"Starting from batch: {start_batch + 1}")
        print(f"Workers: {self.workers}")
        print(f"{'='*70}\n")

        for batch_num in range(start_batch, total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(product_urls))
            batch_urls = product_urls[start_idx:end_idx]

            print(f"\n{'='*70}")
            print(f"BATCH {batch_num + 1}/{total_batches}")
            print(f"{'='*70}")
            print(f"Products in this batch: {len(batch_urls):,}")
            print(f"Range: {start_idx:,} to {end_idx:,}")
            print(f"{'='*70}\n")

            # Scrape this batch
            batch_products = self.scraper.scrape_products_concurrent(batch_urls)

            # Save batch results
            batch_file = self.output_dir / f"batch_{batch_num + 1}_products.json"
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(batch_products, f, indent=2, ensure_ascii=False)
            print(f"\nBatch {batch_num + 1} saved to: {batch_file}")

            all_products.extend(batch_products)

            # Update state
            state = {
                'completed_batches': batch_num + 1,
                'total_batches': total_batches,
                'total_scraped': len(all_products),
                'last_run': datetime.now().isoformat(),
                'workers': self.workers,
                'batch_size': batch_size
            }
            self.save_state(state)
            print(f"Progress saved. Total scraped so far: {len(all_products):,}")

        # Save final combined results
        print(f"\n{'='*70}")
        print(f"ALL BATCHES COMPLETE")
        print(f"{'='*70}")
        print(f"Total products scraped: {len(all_products):,}")

        self.scraper.save_products(all_products, suffix="_final_all_batches")

        # Clean up state file
        if self.state_file.exists():
            self.state_file.unlink()
            print(f"State file cleaned up")

        return all_products


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Batch scraper for large-scale scraping')
    parser.add_argument('--workers', type=int, default=16, help='Number of concurrent workers')
    parser.add_argument('--batch-size', type=int, default=250000, help='Products per batch')
    parser.add_argument('--output-dir', type=str, default='scraped_data', help='Output directory')
    parser.add_argument('--max-pages', type=int, help='Max search pages to scan')
    parser.add_argument('--resume', action='store_true', help='Resume from previous run')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"BATCH SCRAPER - LARGE SCALE SCRAPING")
    print(f"{'='*70}\n")

    # Initialize batch scraper
    batch_scraper = BatchScraper(output_dir=args.output_dir, workers=args.workers)

    # Check for resume
    if args.resume:
        state = batch_scraper.load_state()
        if not state:
            print("No previous run found to resume.")
            return

    # Get product URLs
    print("Fetching product URLs from search...")
    product_urls = batch_scraper.scraper.get_product_urls_from_search(max_pages=args.max_pages)

    if not product_urls:
        print("No product URLs found!")
        return

    # Start batch scraping
    products = batch_scraper.scrape_in_batches(product_urls, batch_size=args.batch_size)

    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Total products: {len(products):,}")
    print(f"Output directory: {args.output_dir}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
