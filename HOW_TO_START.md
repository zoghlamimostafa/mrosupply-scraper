# 🚀 START COMMANDS FOR 1.5M PRODUCT SCRAPE

## ✅ Everything is Ready!

- ✅ Proxy: Rotating Residential (6.6M US IPs) - Working
- ✅ URLs: 1,508,714 products ready
- ✅ Scraper: Optimized (45s timeout, 3 retries)
- ✅ Cost estimate: $2,260 - $3,390

---

## Option 1: Aggressive (Fast but more failures) ⚡

**Best for:** Quick completion, don't mind retrying failures later

```bash
python3 scraper_rotating_residential.py \
  --workers 10 \
  --delay 0.3 \
  --output-dir full_scrape_aggressive
```

**Stats:**
- Time: ~29 days
- Success rate: ~75%
- Failures: ~375,000 (need retry)
- Speed: Fastest

---

## Option 2: Balanced (Recommended) ⭐

**Best for:** Good balance of speed and reliability

```bash
python3 scraper_rotating_residential.py \
  --workers 8 \
  --delay 0.4 \
  --output-dir full_scrape_balanced
```

**Stats:**
- Time: ~35 days
- Success rate: ~92%
- Failures: ~120,000 (manageable)
- Speed: Moderate

---

## Option 3: Conservative (Highest success rate) 🎯

**Best for:** Minimize retries, maximum reliability

```bash
python3 scraper_rotating_residential.py \
  --workers 5 \
  --delay 0.5 \
  --output-dir full_scrape_conservative
```

**Stats:**
- Time: ~43 days
- Success rate: ~95%
- Failures: ~75,000 (minimal)
- Speed: Slower but reliable

---

## Quick Start (Recommended)

```bash
# Use the start script
./START_FULL_SCRAPE.sh
```

Or run directly:

```bash
cd /home/user/Desktop/mrosupply.com

# Start scraping (aggressive mode)
python3 scraper_rotating_residential.py \
  --workers 10 \
  --delay 0.3 \
  --output-dir full_scrape_1.5m
```

---

## Monitor Progress

```bash
# Check output directory
ls -lh full_scrape_1.5m/

# View checkpoint (updates every 50 products)
tail -f full_scrape_1.5m/checkpoint_products.csv

# Count scraped products
wc -l full_scrape_1.5m/checkpoint_products.csv

# Check if scraper is running
ps aux | grep scraper_rotating
```

---

## After Scraping Completes

### 1. Check Results
```bash
cd full_scrape_1.5m/
ls -lh

# View final counts
wc -l products_*.csv
wc -l failed_urls_*.txt
```

### 2. Retry Failed URLs
```bash
python3 retry_failed.py \
  full_scrape_1.5m/failed_urls_*.txt \
  retry_pass2
```

### 3. Retry Again (if needed)
```bash
python3 retry_failed.py \
  retry_pass2/failed_urls_*.txt \
  retry_pass3
```

---

## Stop/Resume

### Stop Scraping
```bash
# Find process
ps aux | grep scraper_rotating

# Kill it
pkill -f scraper_rotating_residential.py
```

**Note:** Checkpoint is saved every 50 products, so you won't lose much progress!

### Resume (Not directly supported)
To resume, you'll need to:
1. Extract already scraped URLs from checkpoint
2. Create new URL list excluding scraped ones
3. Start new scrape with remaining URLs

Or just let it run and retry failures at the end.

---

## Expected Timeline

### Aggressive Mode (29 days)
- Day 1-28: Main scrape (~1.1M products)
- Day 29: First pass complete
- Day 30-32: Retry failures (pass 2)
- Day 33: Retry again (pass 3)
- **Total: ~33 days**

### Balanced Mode (35 days)  
- Day 1-34: Main scrape (~1.4M products)
- Day 35: First pass complete
- Day 36-37: Retry failures
- **Total: ~37 days**

### Conservative Mode (43 days)
- Day 1-42: Main scrape (~1.4M products)
- Day 43: First pass complete
- Day 44: Retry failures
- **Total: ~44 days**

---

## Cost Tracking

Monitor your Webshare dashboard:
- https://proxy.webshare.io/

Expected usage:
- Bandwidth: ~226 GB
- Cost: $2,260 - $3,390
- Per product: ~$0.0015 - $0.0022

---

## Ready to Start?

### Quick Decision Matrix:

**Need it fast?** → Aggressive (29 days, more retries needed)
**Want balance?** → Balanced (35 days, some retries) ⭐
**Want reliability?** → Conservative (43 days, minimal retries)

### Start Now:

```bash
cd /home/user/Desktop/mrosupply.com
./START_FULL_SCRAPE.sh
```

Or choose your preferred mode from the options above!

---

## ✅ All Systems Ready!

Your rotating residential proxy scraper is production-ready for 1.5M products! 🎉
