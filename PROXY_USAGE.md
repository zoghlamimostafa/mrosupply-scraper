# Proxy Usage Guide

The scraper supports proxy rotation to distribute load across multiple proxy servers.

⚠️ **IMPORTANT**: The free proxies from TheSpeedX/PROXY-List are largely non-functional. See [PROXY_ALTERNATIVES.md](PROXY_ALTERNATIVES.md) for better options.

**For most users, running WITHOUT proxies is recommended and works excellently.**

## Features

- **Automatic proxy fetching**: Downloads fresh proxies from TheSpeedX/PROXY-List
- **Proxy validation**: Tests proxies before use to ensure they work
- **Smart rotation**: Distributes requests across working proxies
- **Automatic fallback**: If a proxy fails, automatically tries another
- **Health tracking**: Monitors proxy success/failure rates
- **Load distribution**: Spreads requests evenly across proxy pool

## Command Line Usage

### Basic Usage with Proxies

```bash
python3 fast_scraper.py --use-proxies --max-products 50 --workers 5
```

### With Proxy Validation

Validate more proxies before starting (default: 50):

```bash
python3 fast_scraper.py --use-proxies --validate-proxies 100 --max-products 50
```

### Full Example

```bash
python3 fast_scraper.py \
  --use-proxies \
  --validate-proxies 50 \
  --max-products 100 \
  --workers 10 \
  --output-dir scraped_with_proxies
```

## Arguments

- `--use-proxies`: Enable proxy rotation (required to use proxies)
- `--validate-proxies N`: Number of proxies to test before starting (default: 50)
- `--workers N`: Number of concurrent workers (default: 10)
- `--max-products N`: Limit total products to scrape
- `--max-pages N`: Limit search result pages to fetch
- `--output-dir DIR`: Output directory for results

## How It Works

1. **Fetching**: Downloads HTTP and SOCKS5 proxy lists from TheSpeedX repository
2. **Validation**: Tests a sample of proxies against the target site
3. **Rotation**: Each request uses a random working proxy from the pool
4. **Fallback**: Failed proxies are marked and avoided for subsequent requests
5. **Recovery**: Failed proxies are periodically retried to check if they're working again

## Performance Tips

- Start with fewer workers (5-10) when using proxies to avoid overwhelming them
- Increase `--validate-proxies` for more reliable proxy pool (but slower startup)
- Free proxies may be slow or unreliable - expect some failures
- The scraper automatically handles proxy failures and retries

## Example Output

```
======================================================================
PROXY SETUP
======================================================================
Fetching proxies from TheSpeedX/PROXY-List...
  Fetching http proxies...
    Loaded 15234 http proxies
  Fetching socks5 proxies...
    Loaded 8912 socks5 proxies

Total proxies loaded: 24146

Validating proxies (testing up to 50 proxies)...
  Tested 50/50... Found 12 working

Validation complete: 12 working proxies out of 50 tested
======================================================================

Starting scraping with proxies enabled...
```

## Without Proxies

To run without proxies (direct connection):

```bash
python3 fast_scraper.py --max-products 50 --workers 10
```

## Python API Usage

```python
from fast_scraper import FastMROSupplyScraper

# Create scraper with proxies
scraper = FastMROSupplyScraper(
    output_dir="output",
    max_workers=5,
    use_proxies=True
)

# Setup proxies
scraper.proxy_manager.fetch_proxies()
scraper.proxy_manager.validate_proxies(max_test=50)

# Scrape
product_urls = scraper.get_product_urls_from_search(max_pages=1)
products = scraper.scrape_products_concurrent(product_urls[:20])
scraper.save_products(products)

# View stats
scraper.proxy_manager.print_stats()
```

## Troubleshooting

**No working proxies found:**
- Free proxies can be unreliable
- Try increasing `--validate-proxies` to test more
- The scraper will automatically fall back to direct connection if no proxies work

**Slow performance:**
- Free proxies are often slower than direct connections
- Reduce number of workers with `--workers`
- Some proxies may be in distant locations

**High failure rate:**
- Normal for free proxy lists
- The scraper automatically rotates to working proxies
- Failed proxies are avoided in subsequent requests
