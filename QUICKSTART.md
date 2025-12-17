# QUICKSTART - Deploy & Run in 3 Minutes

## Your Scraper is Ready! 🚀

**Test Results:** ✅ 100% success rate with your 8 proxies

**Time to scrape 1.5M products:** 15-17 days

**Cost:** $9-16 (server rental)

---

## Option 1: Automatic Deployment (Easiest)

### Step 1: Deploy to Server (2 minutes)

```bash
cd /home/user/Desktop/mrosupply.com
./deploy_to_server.sh YOUR_SERVER_IP YOUR_USERNAME
```

**Example:**
```bash
./deploy_to_server.sh 192.168.1.100 root
```

This will:
- ✅ Upload scraper files
- ✅ Install Python & dependencies
- ✅ Set up everything automatically

### Step 2: Start Scraping (30 seconds)

```bash
ssh YOUR_USERNAME@YOUR_SERVER_IP
cd ~/mrosupply_scraper
screen -S scraper
python3 production_scraper.py
```

Press `Ctrl+A` then `D` to detach (keeps running in background)

### Step 3: Check Progress (anytime)

```bash
ssh YOUR_USERNAME@YOUR_SERVER_IP
screen -r scraper
```

Press `Ctrl+A` then `D` to detach again

---

## Option 2: One-Command Start (Ultra Fast)

After deployment, start scraping with one command:

```bash
ssh YOUR_USERNAME@YOUR_SERVER_IP 'cd ~/mrosupply_scraper && screen -dmS scraper python3 production_scraper.py'
```

Done! Scraper is now running in background.

---

## What to Expect

### Phase 1: Collecting URLs (4-8 hours)
```
Page 1: +28 products (Total: 28)
Page 2: +30 products (Total: 58)
...
Total product URLs found: 1,508,692
```

### Phase 2: Scraping Products (14-17 days)
```
Progress: 100/1508692 (0.0%) | Success: 96 (96.0%) | Speed: 0.98/s | ETA: 420.5h
Progress: 1000/1508692 (0.1%) | Success: 967 (96.7%) | Speed: 1.02/s | ETA: 411.2h
...
Progress: 1508692/1508692 (100.0%) | Success: 1435847 (95.2%) | Speed: 0.99/s
```

### Results Saved Every 500 Products
```
💾 Progress saved: 500 products -> products_progress_20251215_120000.json
💾 Progress saved: 1000 products -> products_progress_20251215_123000.json
...
```

### Final Output
```
✅ Saved JSON: products_final_20251215_151034.json (1,435,847 products)
✅ Saved CSV: products_final_20251215_151034.csv
⚠️  Failed URLs: failed_urls_20251215_151034.txt (72,845 failures)
📊 Statistics: statistics_20251215_151034.json
```

---

## Settings (Already Optimized)

**Current configuration in `production_scraper.py`:**
- **Workers:** 12 (perfect for 4-core server)
- **Delay:** 0.8 seconds between requests
- **Speed:** ~1.0 products/second
- **Proxies:** Your 8 working proxies (rotating)

**This gives you:**
- ✅ 15-17 days to complete
- ✅ 90-95% success rate
- ✅ Low risk of bans
- ✅ $9-16 total cost

**Don't change unless needed!**

---

## Monitoring Progress

### Check How Many Products Scraped

```bash
ssh YOUR_USERNAME@YOUR_SERVER_IP "ls -lh ~/mrosupply_scraper/production_data/"
```

### See Live Progress

```bash
ssh YOUR_USERNAME@YOUR_SERVER_IP
screen -r scraper
# Watch it work, then Ctrl+A D to detach
```

### Check Latest Progress File

```bash
ssh YOUR_USERNAME@YOUR_SERVER_IP "tail ~/mrosupply_scraper/production_data/products_progress_*.json | grep url | wc -l"
```

---

## Download Results (After Completion)

### Download Everything

```bash
scp -r YOUR_USERNAME@YOUR_SERVER_IP:~/mrosupply_scraper/production_data ./
```

### Download Just Final Files

```bash
scp YOUR_USERNAME@YOUR_SERVER_IP:~/mrosupply_scraper/production_data/products_final_*.json ./
scp YOUR_USERNAME@YOUR_SERVER_IP:~/mrosupply_scraper/production_data/products_final_*.csv ./
```

---

## Cost Breakdown

```
Server (Hetzner CPX31): $9/month
Running time: 17 days = ~$5
Bandwidth: $0 (included)
Proxies: $0 (you already have them)
Total: ~$5-9

Per product: $0.000003-0.000006
```

**Compare:**
- Your setup: **$5-9 for 17 days** ⭐⭐⭐
- Webshare: $721 for 4 days
- BrightData: $2,500 for 3 days

**You're saving $712-2,491!**

---

## Timeline

| Milestone | Products | Days | % Complete |
|-----------|----------|------|------------|
| Start | 0 | 0 | 0% |
| First 100K | 100,000 | 1.2 | 6.6% |
| Quarter | 377,173 | 4.4 | 25.0% |
| Half | 754,346 | 8.7 | 50.0% |
| Three-quarters | 1,131,519 | 13.1 | 75.0% |
| **Complete** | **1,508,692** | **17.4** | **100%** |

---

## Troubleshooting

### Problem: Can't SSH into server
```bash
# Test connection
ping YOUR_SERVER_IP

# Check SSH
ssh -v YOUR_USERNAME@YOUR_SERVER_IP
```

### Problem: Scraper stopped
```bash
# Check if still running
ssh YOUR_USERNAME@YOUR_SERVER_IP "screen -ls"

# If not running, restart
ssh YOUR_USERNAME@YOUR_SERVER_IP "cd ~/mrosupply_scraper && screen -dmS scraper python3 production_scraper.py"
```

### Problem: Success rate dropping
```bash
# Check current rate in output
screen -r scraper

# If <85%, slow down by editing production_scraper.py:
# WORKERS = 8
# DELAY = 1.2
```

### Problem: Need to stop
```bash
# Graceful stop (saves progress)
screen -r scraper
# Press Ctrl+C

# Force stop (if needed)
screen -X -S scraper quit
```

---

## Files You Have

```
/home/user/Desktop/mrosupply.com/
├── production_scraper.py          ← Main scraper (ready to run)
├── deploy_to_server.sh            ← Deployment script
├── SERVER_SETUP_GUIDE.md          ← Detailed guide
├── QUICKSTART.md                  ← This file
├── PROXY_TEST_RESULTS_SUMMARY.md  ← Your proxy test results
└── requirements.txt               ← Python dependencies
```

---

## Complete Example

```bash
# 1. Deploy (from your local machine)
cd /home/user/Desktop/mrosupply.com
./deploy_to_server.sh 192.168.1.100 root

# 2. Start scraping (one command)
ssh root@192.168.1.100 'cd ~/mrosupply_scraper && screen -dmS scraper python3 production_scraper.py'

# 3. Check progress (daily)
ssh root@192.168.1.100 "screen -r scraper"  # Ctrl+A D to exit

# 4. Download results (after 17 days)
scp -r root@192.168.1.100:~/mrosupply_scraper/production_data ./

# Done! 1.5M products scraped for $5-9
```

---

## Summary

**✅ Everything is ready:**
- Your 8 proxies work (100% success rate tested)
- Scraper optimized for your 4-core, 16GB server
- Deployment script ready
- Will complete in 15-17 days
- Costs only $5-9

**📋 To start:**
1. Run `./deploy_to_server.sh SERVER_IP USER`
2. SSH in and run `python3 production_scraper.py`
3. Wait 15-17 days
4. Download results

**🎯 You'll get:**
- ~1.4M products (95% of 1.5M)
- JSON and CSV formats
- Complete product data
- For less than $10

**Ready to start?** Just run the deploy script! 🚀

---

## Quick Commands Reference

```bash
# Deploy
./deploy_to_server.sh IP USER

# Start (one command from local machine)
ssh USER@IP 'cd ~/mrosupply_scraper && screen -dmS scraper python3 production_scraper.py'

# Check progress
ssh USER@IP "screen -r scraper"  # Ctrl+A D to exit

# Check files
ssh USER@IP "ls -lh ~/mrosupply_scraper/production_data/"

# Download results
scp -r USER@IP:~/mrosupply_scraper/production_data ./

# Stop
ssh USER@IP "screen -X -S scraper quit"
```

---

**Need more details?** Read `SERVER_SETUP_GUIDE.md`

**Need help?** All files include troubleshooting sections.

**Ready to go!** 🎉
