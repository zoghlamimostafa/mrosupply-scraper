# VPS Scraping Guide - 1.5M Products

## Your Scenario

**Hardware:** 16GB RAM, 4 CPU cores
**Target:** 1,508,692 products
**Goal:** Scrape as fast as possible

## Time Estimates

Based on your VPS specs:

| Strategy | Workers | Speed | Time |
|----------|---------|-------|------|
| **Conservative** | 8 | 6.4/s | **65.5 hours** (2.7 days) |
| **Balanced (Recommended)** | 16 | 11.2/s | **37.4 hours** (1.6 days) ⭐ |
| **Aggressive** | 28 | 16.8/s | **24.9 hours** (1.0 days) |
| **Very Aggressive** | 40 | 20.0/s | **21.0 hours** |

**Answer: With your VPS, estimated time is 21-37 hours (0.9-1.6 days)**

### Can We Hit 2 Hours?

**NO** - For 1.5M products in 2 hours, you'd need:
- 350 workers
- 209 products/second
- This would definitely trigger rate limiting and likely get blocked

**Realistic Best Case: 21-24 hours with aggressive settings**

## Recommended Strategy

### Option 1: Balanced Approach (Recommended)

**Best balance of speed and reliability**

```bash
# Use 16 workers
python3 fast_scraper.py --workers 16

# Expected: ~37 hours
```

**Pros:**
- Reliable
- Good speed
- Low memory usage (~0.8GB)
- Low risk of rate limiting

**Cons:**
- Takes 1.6 days

### Option 2: Aggressive Approach (Fastest Reliable)

**Maximum speed without excessive risk**

```bash
# Use 28 workers
python3 fast_scraper.py --workers 28

# Expected: ~25 hours
```

**Pros:**
- Faster (~1 day)
- Still reasonable

**Cons:**
- Higher chance of rate limiting
- Need to monitor more closely

### Option 3: Batch Processing (Safest for Long Runs)

**Break into manageable chunks with resume capability**

```bash
# 7 batches of ~241K products each
# Each batch: ~6 hours
python3 batch_scraper.py --workers 16 --batch-size 241920

# Total: ~37 hours
```

**Pros:**
- Resume capability if interrupted
- Progress checkpoints
- Safer for multi-day runs
- Can review data between batches

**Cons:**
- Same total time as direct approach

## VPS Setup Instructions

### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip -y

# Install required packages
pip3 install beautifulsoup4 requests lxml

# Or use requirements.txt
pip3 install -r requirements.txt
```

### 2. Upload Scraper Files

```bash
# Transfer files to VPS (from your local machine)
scp -r mrosupply.com user@your-vps-ip:/home/user/

# Or use git
git clone <your-repo>
cd mrosupply.com
```

### 3. Run in Background (Important!)

Since scraping takes 21-37 hours, you MUST run in background:

#### Option A: Using `screen` (Recommended)

```bash
# Install screen
sudo apt install screen -y

# Create new screen session
screen -S scraper

# Run scraper
python3 fast_scraper.py --workers 16

# Detach: Press Ctrl+A, then D
# Reattach later: screen -r scraper
```

#### Option B: Using `tmux`

```bash
# Install tmux
sudo apt install tmux -y

# Create session
tmux new -s scraper

# Run scraper
python3 fast_scraper.py --workers 16

# Detach: Press Ctrl+B, then D
# Reattach: tmux attach -t scraper
```

#### Option C: Using `nohup`

```bash
# Run in background
nohup python3 fast_scraper.py --workers 16 > scraper.log 2>&1 &

# Check progress
tail -f scraper.log

# Check if running
ps aux | grep fast_scraper
```

### 4. Monitor Progress

```bash
# Watch log file
tail -f scraper.log

# Check output files
ls -lh scraped_data/

# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top
```

## Optimization Tips for VPS

### 1. Increase File Descriptors

Large number of workers may need more file descriptors:

```bash
# Check current limit
ulimit -n

# Increase limit (temporary)
ulimit -n 4096

# Permanent (add to ~/.bashrc)
echo "ulimit -n 4096" >> ~/.bashrc
```

### 2. Disk Space Management

```bash
# Check space before starting
df -h

# 1.5M products will need ~5-10GB for JSON/CSV
# Ensure you have at least 20GB free
```

### 3. Network Optimization

```bash
# Check network speed
curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 -

# Ensure stable connection
ping -c 10 www.mrosupply.com
```

## Real-World VPS Run Example

### Starting the Scrape

```bash
# SSH into VPS
ssh user@your-vps-ip

# Navigate to directory
cd mrosupply.com

# Start screen session
screen -S scraper

# Run calculator first
python3 vps_calculator.py 1508692 16 4

# Start scraping
python3 batch_scraper.py --workers 16 --batch-size 241920

# Detach from screen: Ctrl+A, then D
```

### Checking Progress

```bash
# Reattach to see live progress
screen -r scraper

# Or check files
ls -lh scraped_data/
cat scraped_data/batch_state.json

# Check how many products so far
grep -c "\"url\"" scraped_data/batch_*_products.json
```

### If Connection Drops

```bash
# SSH back in
ssh user@your-vps-ip

# Reattach to screen
screen -r scraper

# If using batch_scraper, it can resume automatically
python3 batch_scraper.py --workers 16 --batch-size 241920 --resume
```

## Complete VPS Workflow

```bash
# === STEP 1: Setup (5 minutes) ===
ssh user@vps-ip
sudo apt update && sudo apt install python3-pip screen -y
pip3 install beautifulsoup4 requests lxml

# === STEP 2: Upload Files (2 minutes) ===
# (from local machine)
scp -r mrosupply.com user@vps-ip:/home/user/

# === STEP 3: Test (5 minutes) ===
ssh user@vps-ip
cd mrosupply.com
python3 fast_scraper.py --max-products 100 --workers 16

# === STEP 4: Run Calculation (1 minute) ===
python3 vps_calculator.py 1508692 16 4

# === STEP 5: Start Full Scrape (37 hours) ===
screen -S scraper
python3 batch_scraper.py --workers 16 --batch-size 241920
# Ctrl+A, D to detach

# === STEP 6: Monitor (periodically) ===
screen -r scraper  # check progress
# Ctrl+A, D to detach again

# === STEP 7: Download Results ===
# (from local machine, after completion)
scp -r user@vps-ip:/home/user/mrosupply.com/scraped_data ./
```

## Batch Processing Strategy

For 1.5M products, use **7 batches**:

| Batch | Products | Time | Cumulative |
|-------|----------|------|------------|
| 1 | 241,920 | 6h | 6h |
| 2 | 241,920 | 6h | 12h |
| 3 | 241,920 | 6h | 18h |
| 4 | 241,920 | 6h | 24h |
| 5 | 241,920 | 6h | 30h |
| 6 | 241,920 | 6h | 36h |
| 7 | 298,172 | 7h | **43h** |

**Benefits:**
- Can stop/resume anytime
- Progress checkpoints every 6 hours
- Can review data incrementally
- Safer for multi-day runs

## Troubleshooting

### Issue: Too Many Failures

```bash
# Reduce workers
python3 fast_scraper.py --workers 8
```

### Issue: Out of Memory

```bash
# Check memory
free -h

# Reduce workers
python3 fast_scraper.py --workers 10

# Clear cache
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### Issue: Connection Timeout

```bash
# Check connection
ping www.mrosupply.com

# Restart with fewer workers
python3 fast_scraper.py --workers 12
```

### Issue: Disk Full

```bash
# Check space
df -h

# Compress old batches
gzip scraped_data/batch_*_products.json

# Or delete progress files
rm scraped_data/products_progress_*.json
```

## Expected Results

After completion, you'll have:

```
scraped_data/
├── products_final_all_batches.json     # All products (JSON)
├── products_final_all_batches.csv      # All products (CSV)
├── batch_1_products.json               # Batch 1
├── batch_2_products.json               # Batch 2
├── ...
├── batch_7_products.json               # Batch 7
└── failed_urls.txt                     # Any failures
```

**File sizes (estimated):**
- JSON: ~4-6GB
- CSV: ~2-3GB
- Total: ~6-9GB

## Summary

✅ **Your VPS can handle it!**
⏰ **Realistic time: 21-37 hours** (depending on aggressiveness)
💾 **Memory: No problem** (uses <1GB with 16 workers)
🔄 **Use batch processing** for safety and resume capability
📊 **Monitor progress** via screen/tmux

**Recommended command:**
```bash
screen -S scraper
python3 batch_scraper.py --workers 16 --batch-size 241920
```

This gives you **~37 hours** total time with full resume capability!
