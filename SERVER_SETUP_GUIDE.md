# Server Setup & Deployment Guide

## Quick Start (3 Steps)

### Step 1: Deploy to Server

```bash
# Make deploy script executable
chmod +x deploy_to_server.sh

# Deploy (replace with your server details)
./deploy_to_server.sh YOUR_SERVER_IP YOUR_USERNAME

# Example:
./deploy_to_server.sh 192.168.1.100 root
```

### Step 2: Start Scraping

```bash
# SSH into server
ssh YOUR_USERNAME@YOUR_SERVER_IP

# Go to directory
cd ~/mrosupply_scraper

# Start in screen session (keeps running after disconnect)
screen -S scraper
python3 production_scraper.py

# Detach from screen: Ctrl+A, then D
```

### Step 3: Monitor Progress

```bash
# Reattach to see progress
ssh YOUR_USERNAME@YOUR_SERVER_IP
screen -r scraper

# Or check files
ssh YOUR_USERNAME@YOUR_SERVER_IP "ls -lh ~/mrosupply_scraper/production_data/"
```

---

## Detailed Setup Instructions

### Prerequisites

**Your Server Must Have:**
- Ubuntu/Debian Linux (or similar)
- 4 CPU cores
- 16GB RAM
- 50GB+ free disk space
- Internet connection
- SSH access

**Your Local Machine Must Have:**
- SSH client
- The scraper files

### Option A: Automatic Deployment (Recommended)

Use the provided deployment script:

```bash
# From your local machine, in the mrosupply.com directory
chmod +x deploy_to_server.sh
./deploy_to_server.sh SERVER_IP USERNAME

# Example:
./deploy_to_server.sh 192.168.1.100 root
```

The script will:
1. Test SSH connection
2. Create directory on server
3. Upload scraper files
4. Install dependencies (Python, pip, packages)
5. Install screen for background execution

### Option B: Manual Deployment

**1. Upload files to server:**

```bash
# Create directory on server
ssh user@server "mkdir -p ~/mrosupply_scraper"

# Upload files
scp production_scraper.py user@server:~/mrosupply_scraper/
scp requirements.txt user@server:~/mrosupply_scraper/
```

**2. SSH into server:**

```bash
ssh user@server
cd ~/mrosupply_scraper
```

**3. Install dependencies:**

```bash
# Update system
sudo apt-get update

# Install Python and pip
sudo apt-get install -y python3 python3-pip

# Install required packages
pip3 install beautifulsoup4 requests lxml

# Install screen (optional but recommended)
sudo apt-get install -y screen
```

**4. Verify installation:**

```bash
python3 --version        # Should show Python 3.x
pip3 list | grep beautifulsoup4  # Should show beautifulsoup4
```

---

## Running the Scraper

### Method 1: Using Screen (Recommended)

Screen keeps the process running even after you disconnect.

**Start scraping:**

```bash
# Create screen session
screen -S scraper

# Run scraper
cd ~/mrosupply_scraper
python3 production_scraper.py

# Detach from screen (keeps running in background)
# Press: Ctrl+A, then D
```

**Check progress later:**

```bash
# Reattach to screen session
screen -r scraper

# View output, then detach again with Ctrl+A, D
```

**List screen sessions:**

```bash
screen -ls
```

**Kill screen session (if needed):**

```bash
screen -X -S scraper quit
```

### Method 2: Using nohup (Alternative)

```bash
cd ~/mrosupply_scraper
nohup python3 production_scraper.py > scraper.log 2>&1 &

# Check progress
tail -f scraper.log

# Check if running
ps aux | grep production_scraper
```

### Method 3: Direct Run (Not Recommended for Long Jobs)

```bash
cd ~/mrosupply_scraper
python3 production_scraper.py

# This will stop if SSH connection drops!
```

---

## Configuration

### Adjust Settings

Edit `production_scraper.py` line 429-431:

```python
# Current settings (optimized for your 4-core server)
WORKERS = 12          # Number of concurrent workers
DELAY = 0.8           # Seconds between requests
MAX_PRODUCTS = None   # None = all products, or set number for testing
```

### Speed vs Safety Tradeoff:

| Workers | Delay | Speed | Time for 1.5M | Risk |
|---------|-------|-------|---------------|------|
| 8 | 1.0s | 0.67/s | 26 days | Very Low ✅ |
| **12** | **0.8s** | **1.0/s** | **17 days** | **Low** ⭐ |
| 16 | 0.6s | 1.5/s | 12 days | Medium ⚠️ |
| 20 | 0.5s | 2.0/s | 9 days | High ⚠️⚠️ |

**Recommended:** Keep default (12 workers, 0.8s delay)

### Test First (Recommended)

Before running on all 1.5M products, test with smaller batch:

```python
# In production_scraper.py, line 431:
MAX_PRODUCTS = 1000   # Test with 1,000 products first
```

Run test, check success rate. If >90%, proceed with full run:

```python
MAX_PRODUCTS = None   # Scrape all products
```

---

## Monitoring Progress

### Real-time Monitoring

**Method 1: Reattach to screen**

```bash
screen -r scraper
# See live output, press Ctrl+A D to detach
```

**Method 2: Check output files**

```bash
# See what's been saved
ls -lh ~/mrosupply_scraper/production_data/

# Count products scraped so far
grep -c '"url"' ~/mrosupply_scraper/production_data/products_progress_*.json | tail -1

# Check latest progress file
ls -lt ~/mrosupply_scraper/production_data/ | head -5
```

**Method 3: Watch file sizes grow**

```bash
watch -n 10 'ls -lh ~/mrosupply_scraper/production_data/'
# Updates every 10 seconds, shows file sizes growing
```

### Check System Resources

**CPU usage:**

```bash
htop
# Or: top
```

**Memory usage:**

```bash
free -h
```

**Disk space:**

```bash
df -h
```

**Network usage:**

```bash
sudo apt-get install -y iftop
sudo iftop
```

---

## Expected Behavior

### During Scraping

**You should see:**

```
Phase 1: Collecting product URLs...
======================================================================
  Page 1: +28 products (Total: 28)
  Page 2: +30 products (Total: 58)
  ...
  Page 100: +25 products (Total: 5847)

URL Collection Complete!
Total product URLs found: 5,847

Phase 2: Scraping Products
======================================================================
Total products: 5,847
Workers: 12
Estimated time: 65.1 minutes
======================================================================
Progress: 50/5847 (0.9%) | Success: 48 (96.0%) | Speed: 0.92/s | ETA: 105.3m
Progress: 100/5847 (1.7%) | Success: 96 (96.0%) | Speed: 0.95/s | ETA: 100.2m
...
Progress: 5847/5847 (100.0%) | Success: 5520 (94.4%) | Speed: 0.98/s | ETA: 0.0m

  💾 Progress saved: 5000 products -> products_progress_20251215_143052.json
  💾 Progress saved: 5500 products -> products_progress_20251215_150123.json

======================================================================
SAVING FINAL RESULTS
======================================================================
✅ Saved JSON: products_final_20251215_151034.json
   Products: 5,520
✅ Saved CSV: products_final_20251215_151034.csv
⚠️  Failed URLs: failed_urls_20251215_151034.txt
   Count: 327
📊 Statistics: statistics_20251215_151034.json

======================================================================
SCRAPING COMPLETE!
======================================================================
Total products targeted: 5,847
Successfully scraped:    5,520 (94.4%)
Failed:                  327 (5.6%)
Total time:              98.5 minutes (1.64 hours)
Average speed:           0.93 products/second
```

### Progress Files

**Saved every 500 products:**
- `products_progress_YYYYMMDD_HHMMSS.json`

**At completion:**
- `products_final_YYYYMMDD_HHMMSS.json` - All products (JSON)
- `products_final_YYYYMMDD_HHMMSS.csv` - All products (CSV)
- `failed_urls_YYYYMMDD_HHMMSS.txt` - URLs that failed
- `statistics_YYYYMMDD_HHMMSS.json` - Scraping statistics

### Expected Timeline

**For 1,508,692 products with default settings (12 workers, 0.8s delay):**

```
Phase 1 (URL collection): 4-8 hours
Phase 2 (Scraping): 14-17 days
Total: ~15-17 days
```

**Progress milestones:**

| Products | Time Elapsed | % Complete |
|----------|--------------|------------|
| 100,000 | ~1.2 days | 6.6% |
| 250,000 | ~2.9 days | 16.6% |
| 500,000 | ~5.8 days | 33.1% |
| 750,000 | ~8.7 days | 49.7% |
| 1,000,000 | ~11.6 days | 66.3% |
| 1,250,000 | ~14.5 days | 82.9% |
| 1,500,000 | ~17.4 days | 99.4% |

---

## Troubleshooting

### Problem: Scraper Stopped/Crashed

**Check if still running:**

```bash
# Check screen sessions
screen -ls

# Check process
ps aux | grep production_scraper

# Check log (if using nohup)
tail -50 scraper.log
```

**Resume:**

```bash
# If screen session exists, reattach
screen -r scraper

# If crashed, restart
cd ~/mrosupply_scraper
screen -S scraper
python3 production_scraper.py
```

### Problem: Low Success Rate (<85%)

**Possible causes:**
1. Proxies getting blocked
2. Speed too aggressive
3. Site changes

**Solutions:**

```python
# Slow down in production_scraper.py
WORKERS = 8           # Reduce workers
DELAY = 1.2           # Increase delay
```

**Check current success rate:**

```bash
# Look at recent progress output
screen -r scraper
```

### Problem: Out of Disk Space

**Check space:**

```bash
df -h
```

**Free up space:**

```bash
# Compress old progress files
gzip ~/mrosupply_scraper/production_data/products_progress_*.json

# Or delete old progress files (keep final only)
rm ~/mrosupply_scraper/production_data/products_progress_*.json
```

### Problem: Server Running Slow

**Check resources:**

```bash
# CPU
top

# Memory
free -h

# Disk I/O
iostat
```

**If memory is full:**

```bash
# Reduce workers
# Edit production_scraper.py, change WORKERS to 8 or 6
```

### Problem: SSH Connection Lost

**Don't worry!** If you used screen, scraper keeps running.

**Reconnect:**

```bash
ssh user@server
screen -r scraper
```

### Problem: Need to Stop Scraping

**Graceful stop:**

```bash
# Reattach to screen
screen -r scraper

# Press Ctrl+C
# This will save current progress before stopping
```

**Force kill (not recommended):**

```bash
# Find process ID
ps aux | grep production_scraper

# Kill it
kill -9 [PID]

# Or kill screen session
screen -X -S scraper quit
```

---

## Downloading Results

### Download All Data

**From your local machine:**

```bash
# Download entire production_data directory
scp -r user@server:~/mrosupply_scraper/production_data ./

# Or compress first for faster transfer
ssh user@server "cd ~/mrosupply_scraper && tar -czf production_data.tar.gz production_data/"
scp user@server:~/mrosupply_scraper/production_data.tar.gz ./
tar -xzf production_data.tar.gz
```

### Download Specific Files

```bash
# Just the final JSON
scp user@server:~/mrosupply_scraper/production_data/products_final_*.json ./

# Just the final CSV
scp user@server:~/mrosupply_scraper/production_data/products_final_*.csv ./

# Statistics
scp user@server:~/mrosupply_scraper/production_data/statistics_*.json ./
```

### Check File Sizes Before Download

```bash
ssh user@server "ls -lh ~/mrosupply_scraper/production_data/"
```

**Expected sizes for 1.5M products:**
- JSON: 3-5 GB
- CSV: 2-3 GB
- Total: 5-8 GB

---

## Optimization Tips

### Speed Up (More Aggressive)

**Only if success rate is >95%:**

```python
# In production_scraper.py
WORKERS = 16          # Increase workers
DELAY = 0.6           # Decrease delay
# Expected: ~12 days for 1.5M
```

### Slow Down (More Conservative)

**If getting failures or bans:**

```python
# In production_scraper.py
WORKERS = 8           # Decrease workers
DELAY = 1.2           # Increase delay
# Expected: ~26 days for 1.5M
```

### Batch Processing (For Very Large Jobs)

**Split into batches of 100K products:**

```python
# Run 1: First 100K
MAX_PRODUCTS = 100000

# Run 2: Next 100K
# Modify scraper to skip first 100K...
# (Or implement resume from checkpoint)
```

---

## Cost Breakdown

### Server Costs (Example: Hetzner VPS)

| Server | Specs | Cost/Month | Cost for 17 days |
|--------|-------|------------|------------------|
| **CPX21** | 3 vCPU, 4GB | €7.56 | ~€4.28 |
| **CPX31** | 4 vCPU, 8GB | €14.28 | ~€8.09 |
| **CPX41** | 8 vCPU, 16GB | €27.60 | ~€15.64 |

**Recommended: CPX31 (4 vCPU, 8GB) = ~$9 for 17 days**

### Total Cost Estimate

```
Server (17 days): $9-16
Proxies: $0 (already have)
Bandwidth: $0 (included)
Total: $9-16

Per product: $0.000006-0.000011
```

**Compare to alternatives:**
- Webshare (4 days): $721
- BrightData (3 days): $2,500
- **Your setup (17 days): $9-16** ⭐⭐⭐

---

## Summary Checklist

**Before Starting:**
- [ ] Server ready (4 cores, 16GB RAM)
- [ ] SSH access working
- [ ] 50GB+ free disk space
- [ ] Files uploaded to server

**Starting:**
- [ ] Dependencies installed
- [ ] Screen or nohup ready
- [ ] Configuration checked
- [ ] Test run successful (100-1000 products)

**During Running:**
- [ ] Check progress daily
- [ ] Monitor success rate (should be >85%)
- [ ] Check disk space weekly
- [ ] Verify progress files being created

**After Complete:**
- [ ] Download results
- [ ] Verify data quality
- [ ] Check statistics
- [ ] Retry failed URLs if needed
- [ ] Clean up server (optional)

---

## Quick Reference Commands

```bash
# Deploy
./deploy_to_server.sh SERVER_IP USER

# Start scraping
ssh USER@SERVER "cd ~/mrosupply_scraper && screen -dmS scraper python3 production_scraper.py"

# Check progress
ssh USER@SERVER "screen -r scraper"  # Press Ctrl+A D to detach

# Check files
ssh USER@SERVER "ls -lh ~/mrosupply_scraper/production_data/"

# Download results
scp -r USER@SERVER:~/mrosupply_scraper/production_data ./

# Stop scraping
ssh USER@SERVER "screen -X -S scraper quit"
```

---

## Need Help?

**Check:**
1. Screen session is running: `screen -ls`
2. Process is running: `ps aux | grep production`
3. Files are being created: `ls -lt production_data/`
4. Success rate is good: `screen -r scraper`
5. Disk space available: `df -h`

**Most common issues:**
- SSH disconnected → Use screen
- Out of disk space → Clean old files
- Low success rate → Reduce speed
- Slow progress → Increase workers (if resources available)

---

## Estimated Timeline Summary

**Default Configuration (12 workers, 0.8s delay):**

```
URL Collection:    4-8 hours
Scraping 1.5M:     14-17 days
Total:             ~15-17 days
Cost:              $9-16
Success Rate:      90-95%
```

**This is the sweet spot for:**
- ✅ Reasonable speed
- ✅ High success rate
- ✅ Low cost
- ✅ Proven to work with your proxies

**Ready to start!** 🚀
