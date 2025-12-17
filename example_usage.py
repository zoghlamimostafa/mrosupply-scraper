#!/usr/bin/env python3
"""
Example usage of the MROSupply scraper as a Python library
"""

from scraper import MROSupplyScraper


def example_1_scrape_local_file():
    """Example 1: Scrape a local HTML file"""
    print("=== Example 1: Scrape Local File ===")

    scraper = MROSupplyScraper(output_dir="example_output")

    # Scrape the example file
    product = scraper.scrape_local_file(
        "755-702-413139 Rotary Union Deublin _ MROSupply.com - MROSupply.com.html"
    )

    # Print product details
    print(f"Product: {product['name']}")
    print(f"Brand: {product['brand']}")
    print(f"Price: {product['price']}")
    print(f"Specifications: {len(product['specifications'])} found")
    print(f"Images: {len(product['images'])} found")
    print(f"Documents: {len(product['documents'])} found")

    # Save to files
    scraper.save_products([product], suffix="_example1")
    print("\n")


def example_2_scrape_specific_urls():
    """Example 2: Scrape specific product URLs"""
    print("=== Example 2: Scrape Specific URLs ===")

    scraper = MROSupplyScraper(output_dir="example_output")

    # Define specific product URLs you want to scrape
    product_urls = [
        "https://www.mrosupply.com/hydraulics-and-pneumatics/99986_755-702-413139_deublin/",
        # Add more URLs here...
    ]

    # Scrape the products
    products = scraper.scrape_products(product_urls, delay=1.0)

    # Print summary
    print(f"Scraped {len(products)} products")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['name']} - {product['price']}")

    # Save to files
    scraper.save_products(products, suffix="_example2")
    print("\n")


def example_3_scrape_search_limited():
    """Example 3: Scrape limited products from search"""
    print("=== Example 3: Scrape from Search (Limited) ===")

    scraper = MROSupplyScraper(output_dir="example_output")

    # Get product URLs from search (limit to first 2 pages)
    product_urls = scraper.get_product_urls_from_search(
        per_page=120,
        max_pages=2
    )

    print(f"Found {len(product_urls)} product URLs")

    # Scrape only first 10 products
    limited_urls = product_urls[:10]
    products = scraper.scrape_products(limited_urls, delay=1.0)

    # Save to files
    scraper.save_products(products, suffix="_example3")

    # Analyze the data
    total_specs = sum(len(p['specifications']) for p in products)
    total_images = sum(len(p['images']) for p in products)
    total_docs = sum(len(p['documents']) for p in products)

    print(f"Total products: {len(products)}")
    print(f"Total specifications: {total_specs}")
    print(f"Total images: {total_images}")
    print(f"Total documents: {total_docs}")
    print("\n")


def example_4_extract_specific_data():
    """Example 4: Extract specific data from scraped products"""
    print("=== Example 4: Extract Specific Data ===")

    scraper = MROSupplyScraper(output_dir="example_output")

    # Scrape a product
    product = scraper.scrape_local_file(
        "755-702-413139 Rotary Union Deublin _ MROSupply.com - MROSupply.com.html"
    )

    # Extract specific information
    print(f"Product Name: {product['name']}")
    print(f"Brand: {product['brand']}")
    print(f"MPN: {product['mpn']}")
    print(f"Price: {product['price']}")
    print(f"Category: {product['category']}")

    # Print all specifications
    print("\nSpecifications:")
    for key, value in product['specifications'].items():
        print(f"  - {key}: {value}")

    # Print all images
    print("\nImages:")
    for img_url in product['images']:
        print(f"  - {img_url}")

    # Print all documents
    print("\nDocuments:")
    for doc in product['documents']:
        print(f"  - {doc['name']}: {doc['url']}")

    print("\n")


def example_5_custom_filtering():
    """Example 5: Scrape and filter products"""
    print("=== Example 5: Scrape and Filter Products ===")

    scraper = MROSupplyScraper(output_dir="example_output")

    # Scrape local file
    product = scraper.scrape_local_file(
        "755-702-413139 Rotary Union Deublin _ MROSupply.com - MROSupply.com.html"
    )

    # Filter products by criteria
    # Example: Check if product has documents
    has_documents = len(product['documents']) > 0
    print(f"Product has documents: {has_documents}")

    # Example: Check if product has specific specifications
    has_flow_spec = any('flow' in key.lower() for key in product['specifications'].keys())
    print(f"Product has flow specifications: {has_flow_spec}")

    # Example: Check if product is in stock
    in_stock = "InStock" in product['availability']
    print(f"Product is in stock: {in_stock}")

    # Example: Extract price as float
    try:
        price_str = product['price'].replace('$', '').replace(',', '')
        price_float = float(price_str)
        print(f"Price as number: ${price_float:.2f}")
    except (ValueError, AttributeError):
        print("Could not parse price")

    print("\n")


if __name__ == '__main__':
    # Run examples
    print("MROSupply Scraper - Usage Examples\n")

    # Example 1: Scrape a local file
    example_1_scrape_local_file()

    # Example 2: Scrape specific URLs
    # Uncomment to run (requires internet connection):
    # example_2_scrape_specific_urls()

    # Example 3: Scrape from search with limits
    # Uncomment to run (requires internet connection and takes time):
    # example_3_scrape_search_limited()

    # Example 4: Extract specific data
    example_4_extract_specific_data()

    # Example 5: Custom filtering
    example_5_custom_filtering()

    print("All examples completed!")
