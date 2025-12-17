# SAFE Scraping Guide - Avoid Getting Banned

## ⚠️ IMPORTANT: Rate Limits Are Real

In our tests, we **DID get rate limited** with aggressive settings:
- 10 workers, 0.2s delay: Got 429 errors (Too Many Requests)
- Success rate dropped to 92% (46/50 products)
- Some requests were rejected

**6 products/second IS TOO AGGRESSIVE and can get you banned!**

## How to Avoid Bans

### 1. Use Conservative Settings (RECOMMENDED)

```bash
# SAFE: 3 workers, 1 second delay = ~2 products/second
python3 fast_scraper.py --max-products 100 --workers 3 --delay 1.0

# SAFER: 2 workers, 2 second delay = ~1 product/second
python3 fast_scraper.py --max-products 100 --workers 2 --delay 2.0

# SAFEST: 1 worker, 3 second delay = ~0.3 products/second
python3 fast_scraper.py --max-products 100 --workers 1 --delay 3.0
```

### 2. Respect Rate Limits

**Safe Speed Guidelines:**
- ✅ **0.5-2 products/second** - Safe for most sites
- ⚠️ **2-5 products/second** - Risky, may get throttled
- ❌ **5+ products/second** - Very likely to get banned

**Our new defaults (SAFE):**
- Workers: 3 (down from 10)
- Delay: 1.0 seconds (up from 0.2s)
- Speed: ~2 products/second

### 3. Performance vs Safety

| Workers | Delay | Speed | Safety | Use Case |
|---------|-------|-------|--------|----------|
| 1 | 3.0s | 0.3/s | ✅✅✅ Safest | Production, long-term |
| 2 | 2.0s | 1.0/s | ✅✅ Very Safe | Daily scraping |
| 3 | 1.0s | 2.0/s | ✅ Safe | **RECOMMENDED** |
| 5 | 0.5s | 5.0/s | ⚠️ Risky | Testing only |
| 10 | 0.2s | 10/s | ❌ Banned | Don't use! |

### 4. Calculate Your Speed

```
Speed = Workers / Delay
```

**Examples:**
- 3 workers, 1s delay = 3 products/second
- 2 workers, 2s delay = 1 product/second
- 1 worker, 2s delay = 0.5 products/second

### 5. Time Estimates (Safe Settings)

With **3 workers, 1s delay** (~2 products/sec):

| Products | Time |
|----------|------|
| 10 | 5 seconds |
| 100 | 50 seconds (~1 min) |
| 500 | 4-5 minutes |
| 1000 | 8-10 minutes |
| 5000 | 40-50 minutes |

## Recommended Commands

### Quick Test (10 products)
```bash
python3 fast_scraper.py --max-products 10 --workers 2 --delay 1.0
# ~5 seconds
```

### Small Job (100 products)
```bash
python3 fast_scraper.py --max-products 100 --workers 3 --delay 1.0 --output-dir small_job
# ~50 seconds
```

### Medium Job (500 products)
```bash
python3 fast_scraper.py --max-products 500 --workers 3 --delay 1.0 --output-dir medium_job
# ~4-5 minutes
```

### Large Job (1000+ products) - SAFE for long-term
```bash
python3 fast_scraper.py --max-products 1000 --workers 2 --delay 2.0 --output-dir large_job
# ~8-10 minutes, very safe
```

### Production (Safest)
```bash
python3 fast_scraper.py --max-products 5000 --workers 1 --delay 3.0 --output-dir production
# ~4-5 hours, but won't get banned
```

## Warning Signs You're Going Too Fast

Watch for these in the output:

```
⚠️ Rate limited! Waiting 5s before retry...
⚠️ 429 Client Error: Too Many Requests
⚠️ Multiple failed requests
⚠️ Success rate < 95%
```

**If you see these: STOP and use slower settings!**

## Best Practices

### ✅ DO:
- Start with conservative settings (3 workers, 1s delay)
- Monitor success rate (should be >95%)
- Scrape during off-peak hours (night/early morning)
- Take breaks between large jobs
- Use randomized delays (built-in)
- Respect robots.txt (if applicable)

### ❌ DON'T:
- Use 10+ workers without delays
- Scrape faster than 3 products/second
- Run multiple instances simultaneously
- Scrape 24/7 continuously
- Ignore 429 errors
- Retry failed requests immediately

## What Happens If You Get Banned?

**Temporary Ban (Soft):**
- 429 errors for 1-24 hours
- Your IP is rate-limited
- Solution: Wait it out, then use slower settings

**Permanent Ban (Hard):**
- All requests blocked (403/404 errors)
- IP blacklisted
- Solution: Change IP (VPN, proxy, new ISP)

**How to avoid:**
- Use the safe settings above
- Never exceed 2-3 products/second
- Add longer delays for large jobs

## Monitoring Your Scraping

The scraper shows real-time stats:

```
Progress: 50/100 (50%) | Success: 48 | Failed: 2 | Rate: 2.1/s
```

**Good signs:**
- Success rate > 95%
- Rate: 1-2 products/second
- Few or no "Rate limited" messages

**Bad signs:**
- Success rate < 90%
- Rate: 5+ products/second
- Frequent "Rate limited" messages
- 429 errors

## Example Safe Usage

```bash
# 1. Start with a test
python3 fast_scraper.py --max-products 10 --workers 2 --delay 1.0

# 2. If successful (>95%), try medium
python3 fast_scraper.py --max-products 100 --workers 3 --delay 1.0

# 3. If still good, go larger with safety margin
python3 fast_scraper.py --max-products 500 --workers 3 --delay 1.5

# 4. For production, be conservative
python3 fast_scraper.py --max-products 1000 --workers 2 --delay 2.0
```

## Technical Details

### How the delay works:

```python
# Each request waits:
base_delay = 1.0 seconds (configurable)
random_offset = 0-0.1 seconds (built-in randomization)
total_delay = 1.0-1.1 seconds per request

# With 3 workers:
3 requests every ~1 second = 2-3 products/second
```

### Built-in protections:

- Automatic retry on 429 errors (with backoff)
- Random delays to avoid patterns
- Configurable workers and delays
- Progress monitoring

## Summary

### SAFE Settings (Use These):
```bash
# Default (RECOMMENDED)
python3 fast_scraper.py --max-products 100 --workers 3 --delay 1.0

# Extra Safe
python3 fast_scraper.py --max-products 100 --workers 2 --delay 2.0

# Ultra Safe (Production)
python3 fast_scraper.py --max-products 100 --workers 1 --delay 3.0
```

### UNSAFE Settings (Don't Use):
```bash
# TOO FAST - Will get banned!
python3 fast_scraper.py --max-products 100 --workers 10 --delay 0.2
```

**Bottom line: Slower is safer. The default settings (3 workers, 1s delay) are a good balance between speed and safety.**
