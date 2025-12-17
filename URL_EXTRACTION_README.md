# URL Extraction Tool - Get All 1.5M Product URLs

## Overview

This tool extracts **ALL product URLs** from mrosupply.com sitemaps (1-151) and saves them to a file. This is much faster than crawling search pages!

## Quick Start

### Option 1: Easy Way (Recommended)

```bash
./extract_all_urls.sh
```

This will:
- Download all 151 sitemaps from the web
- Extract all ~1.5M product URLs
- Save as both TXT and JSON
- Takes ~2-5 minutes

### Option 2: Manual Way

```bash
# Extract ALL URLs (downloads from web)
python3 get_all_urls.py \
  --sitemap-start 1 \
  --sitemap-end 151 \
  --format both

# Use local sitemap files if you have them
python3 get_all_urls.py \
  --sitemap-start 1 \
  --sitemap-end 151 \
  --local-sitemaps /path/to/sitemaps \
  --format both
```

## Output Files

After running, you'll get:

```
all_product_urls_20251215_225856.txt       # All URLs (one per line)
all_product_urls_20251215_225856.json      # All URLs (JSON array)
url_extraction_summary_20251215_225856.txt # Summary info
```

## Examples

### Extract first 10 sitemaps only (quick test)

```bash
python3 get_all_urls.py \
  --sitemap-start 1 \
  --sitemap-end 10 \
  --format txt
```

### Extract specific range (e.g., sitemaps 50-100)

```bash
python3 get_all_urls.py \
  --sitemap-start 50 \
  --sitemap-end 100 \
  --format both
```

### Use local sitemap files

```bash
python3 get_all_urls.py \
  --sitemap-start 1 \
  --sitemap-end 151 \
  --local-sitemaps /home/user/Desktop/mrosupply.com \
  --format both
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--sitemap-start` | Starting sitemap number | 1 |
| `--sitemap-end` | Ending sitemap number | 151 |
| `--local-sitemaps` | Path to local sitemap directory | None (downloads from web) |
| `--format` | Output format: txt, json, or both | both |
| `--output` | Custom output filename (without extension) | all_product_urls |

## What You Get

- **~1.5 million product URLs** extracted in 2-5 minutes
- **Ready to scrape** - Use these URLs with your scraper
- **Two formats** - TXT (one URL per line) and JSON (array)
- **Summary file** - Shows statistics and sample URLs

## Next Steps

Once you have the URL file, you can:

1. **Scrape first 10K for testing:**
   ```bash
   head -10000 all_product_urls_*.txt > first_10k_urls.txt
   # Then use with your scraper
   ```

2. **Split into batches:**
   ```bash
   split -l 10000 all_product_urls_*.txt batch_
   # Creates batch_aa, batch_ab, batch_ac, etc.
   ```

3. **Use with sitemap scraper:**
   ```bash
   python3 crawl4ai_scraper.py \
     --url-file all_product_urls_*.txt \
     --webshare-api-key YOUR_KEY
   ```

## Time Estimates

| Sitemaps | Estimated URLs | Extraction Time |
|----------|---------------|-----------------|
| 1-10 | ~100,000 | 30 seconds |
| 1-50 | ~500,000 | 1-2 minutes |
| 1-151 (ALL) | ~1,500,000 | 2-5 minutes |

## FAQ

**Q: Do I need local sitemap files?**
A: No. The script will download them from the web automatically.

**Q: How many URLs per sitemap?**
A: Approximately 10,000 URLs per sitemap file.

**Q: Can I stop and resume?**
A: No need! The entire extraction takes only 2-5 minutes.

**Q: What if some sitemaps fail?**
A: The script continues with the rest and shows which ones failed.

**Q: How do I verify the extraction worked?**
A: Check the summary file - it shows total URLs and samples.

## Troubleshooting

**Error: "No URLs extracted!"**
- Check your internet connection
- Try with `--local-sitemaps` if you have local files

**Error: Timeout downloading sitemap**
- The site may be slow - script will retry
- Check if sitemap exists: `https://www.mrosupply.com/sitemap-product-1.xml`

**Want only 10K URLs for testing?**
```bash
python3 get_all_urls.py --sitemap-start 1 --sitemap-end 1 --format txt
```

## File Format

### TXT Format
```
https://www.mrosupply.com/bearings/96760388_cm-spw2213-206n1_ntn-bearing/
https://www.mrosupply.com/bearings/96760389_cm-spw2215-208n1_ntn-bearing/
https://www.mrosupply.com/bearings/96760390_cm-spw2217-215n1_ntn-bearing/
...
```

### JSON Format
```json
[
  "https://www.mrosupply.com/bearings/96760388_cm-spw2213-206n1_ntn-bearing/",
  "https://www.mrosupply.com/bearings/96760389_cm-spw2215-208n1_ntn-bearing/",
  "https://www.mrosupply.com/bearings/96760390_cm-spw2217-215n1_ntn-bearing/",
  ...
]
```

---

**Ready to extract all URLs? Run:**
```bash
./extract_all_urls.sh
```
