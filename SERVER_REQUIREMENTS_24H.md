# Server Requirements for 24-Hour Scrape

## Target: 1,500,000 Products in 24 Hours

---

## Performance Calculations

### Required Rate
```
Total products: 1,500,000
Time available: 24 hours = 86,400 seconds
Required rate: 17.36 products/second

With 90% success rate:
Requests needed: 1,666,667
Required rate: 19.3 requests/second
```

### Per-Worker Performance
```
Average request time: 1.2 seconds (network + processing)
Requests per worker: 0.83 requests/second
Workers needed: 19.3 / 0.83 = 23 workers (minimum)

With safety margin (rate limits, retries):
Recommended: 40-50 workers
```

---

## Hardware Specifications

### Minimum (Not Recommended)
```yaml
CPU: 4 cores (8 threads)
RAM: 8 GB
Disk: 50 GB SSD
Network: 50 Mbps
Workers: 20-30
Expected time: 30-36 hours
Success rate: 85-90%
```

### Recommended (24-Hour Target)
```yaml
CPU: 8 cores (16 threads)
RAM: 16-32 GB
Disk: 100 GB NVMe SSD
Network: 100 Mbps
Workers: 40-50
Expected time: 20-24 hours
Success rate: 90-95%
```

### Optimal (20-Hour Target)
```yaml
CPU: 16 cores (32 threads)
RAM: 32 GB
Disk: 200 GB NVMe SSD
Network: 1 Gbps
Workers: 60-80
Expected time: 18-20 hours
Success rate: 95%+
```

---

## Server Providers Comparison

### 1. Hetzner (Best Value) ⭐ RECOMMENDED
**CCX32**
- vCPU: 8 cores (AMD EPYC)
- RAM: 32 GB
- Disk: 240 GB NVMe
- Network: 1 Gbps
- Location: Germany/Finland
- **Cost: €44.90/month (~$1.50/day)**

**Pros:**
- Excellent price/performance
- NVMe SSD (fast I/O)
- Generous bandwidth (20TB included)
- European IPs (less blocked)

**Cons:**
- European locations only
- Requires account verification

**Setup:**
```bash
# Order at: https://www.hetzner.com/cloud
# Select: CCX32
# OS: Ubuntu 22.04
# Setup time: 5 minutes
```

---

### 2. OVH (Good Alternative)
**Comfort**
- vCPU: 8 cores
- RAM: 32 GB
- Disk: 200 GB NVMe
- Network: 1 Gbps
- Location: EU/Canada/US
- **Cost: ~€35/month (~$1.17/day)**

**Pros:**
- Cheaper than Hetzner
- Multiple locations
- Anti-DDoS included

**Cons:**
- Slightly slower CPUs
- Limited IPv4

---

### 3. DigitalOcean (Easy Setup)
**CPU-Optimized 16GB**
- vCPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- Network: 200 Mbps
- Location: Global
- **Cost: $80/month (~$2.67/day)**

**Pros:**
- Easy setup
- Good documentation
- Global locations
- $200 free credit for new accounts

**Cons:**
- More expensive
- Only 16GB RAM
- Slower disk I/O

---

### 4. Vultr (Good Balance)
**High Performance 8GB**
- vCPU: 4 cores (3.8GHz)
- RAM: 8 GB
- Disk: 128 GB NVMe
- Network: 4 Gbps
- Location: Global
- **Cost: $48/month (~$1.60/day)**

**Pros:**
- Fast CPUs (3.8GHz)
- NVMe storage
- Great network speed
- Global locations

**Cons:**
- Only 4 cores (need 8)
- Only 8GB RAM (need 16GB+)

**Better option:** High Performance 16GB ($96/month)

---

### 5. Linode (Now Akamai)
**Dedicated 16GB**
- vCPU: 8 cores
- RAM: 16 GB
- Disk: 320 GB SSD
- Network: 8 Gbps
- Location: Global
- **Cost: $96/month (~$3.20/day)**

**Pros:**
- Excellent network (8 Gbps)
- Large disk
- Reliable

**Cons:**
- More expensive
- Not NVMe

---

### 6. AWS (Enterprise)
**c6i.4xlarge**
- vCPU: 16 cores
- RAM: 32 GB
- Disk: EBS (charged separately)
- Network: Up to 12.5 Gbps
- Location: Global
- **Cost: ~$0.68/hour (~$16.32/day)**

**Pros:**
- Powerful
- Global reach
- Enterprise features

**Cons:**
- Very expensive
- Complex pricing
- Egress charges

---

### 7. Azure (Enterprise)
**F16s v2**
- vCPU: 16 cores
- RAM: 32 GB
- Disk: Premium SSD (charged separately)
- Network: Up to 12.5 Gbps
- Location: Global
- **Cost: ~$0.72/hour (~$17.28/day)**

**Pros:**
- Powerful
- Global reach
- Integration with Azure Functions

**Cons:**
- Most expensive
- Complex setup
- Egress charges

---

## Cost Comparison (24-Hour Scrape)

| Provider | Instance | Cost/Day | Total Cost | Value Rating |
|----------|----------|----------|------------|--------------|
| Hetzner | CCX32 | $1.50 | $1.50 | ⭐⭐⭐⭐⭐ |
| OVH | Comfort | $1.17 | $1.17 | ⭐⭐⭐⭐⭐ |
| DigitalOcean | CPU-16GB | $2.67 | $2.67 | ⭐⭐⭐⭐ |
| Vultr | HP-16GB | $3.20 | $3.20 | ⭐⭐⭐ |
| Linode | Ded-16GB | $3.20 | $3.20 | ⭐⭐⭐ |
| AWS | c6i.4xlarge | $16.32 | $16.32 | ⭐⭐ |
| Azure | F16s v2 | $17.28 | $17.28 | ⭐⭐ |

**Plus proxy costs:** ~$20-30 for bandwidth

---

## Recommended Configuration

### Server: Hetzner CCX32
```yaml
Provider: Hetzner
Instance: CCX32
CPU: 8 cores
RAM: 32 GB
Disk: 240 GB NVMe
Network: 1 Gbps
Cost: $1.50/day
```

### Software Configuration
```bash
# .env settings for 24h
WORKERS=50
DELAY=0.2
MAX_RETRIES=3
RATE_LIMIT_THRESHOLD=20
COOLDOWN_MINUTES=5
ADAPTIVE_RATE_LIMIT=True

# Memory optimization
MEMORY_THRESHOLD_MB=28000  # Leave 4GB for system
GC_THRESHOLD=10000  # Garbage collect every 10k products

# Network optimization
REQUEST_TIMEOUT=15
CONNECTION_POOL_SIZE=100
KEEP_ALIVE=True
```

### Proxy Configuration

**Option 1: Webshare Premium**
- Plan: Residential Rotating
- Concurrent connections: 50+
- Bandwidth: ~75GB needed
- Cost: ~$25

**Option 2: Smartproxy**
- Plan: Residential
- Concurrent connections: Unlimited
- Traffic: 8GB (~$80) or 40GB (~$360)
- Better for aggressive scraping

**Option 3: Oxylabs**
- Plan: Residential Proxies
- Concurrent: Unlimited
- Traffic-based pricing
- Cost: ~$300 for 40GB

**Recommendation:** Webshare Premium ($25) for budget, Smartproxy for reliability

---

## Bandwidth Requirements

### Calculation
```
Average size per product:
- HTML page: ~30 KB
- Images metadata: ~10 KB
- Request/response overhead: ~10 KB
Total: ~50 KB per product

For 1.5M products:
1,500,000 × 50 KB = 75 GB

With retries (10% failure, 1 retry):
75 GB × 1.1 = 82.5 GB

Recommended: 100 GB bandwidth
```

### Bandwidth Distribution
- Proxy egress: 82.5 GB
- Server ingress: 82.5 GB (usually free)
- Results storage: ~3 GB (JSON/CSV)
- Logs: ~500 MB

**Total network usage:** ~85 GB

---

## Storage Requirements

### Disk Usage
```
Checkpoint file: ~3 GB (1.5M products × 2KB avg)
Results CSV: ~2 GB
Results JSON: ~3 GB
Failed URLs: ~100 MB
Logs: ~500 MB
Backups: ~6 GB (2 checkpoint copies)
System: ~10 GB

Total: ~25 GB
Recommended: 50-100 GB SSD
```

### I/O Performance Needed
- Write speed: 100+ MB/s (NVMe recommended)
- IOPS: 5,000+ (for checkpoint updates)
- Latency: <1ms (NVMe vs SSD)

**Recommendation:** NVMe SSD for 30% faster checkpoint saves

---

## Memory Requirements

### Memory Usage Breakdown
```
Per worker:
- Python interpreter: 50 MB base
- BeautifulSoup parsing: 100-200 MB per worker
- Request/response buffers: 50 MB
Total per worker: ~300 MB

For 50 workers:
50 × 300 MB = 15 GB

Additional:
- System: 2 GB
- Checkpoint buffer: 1 GB
- Cache: 2 GB
- Headroom: 4 GB

Total: 24 GB minimum
Recommended: 32 GB
```

### Memory Optimization
```python
# Enable garbage collection
import gc
gc.enable()

# Periodic cleanup
if products_count % 10000 == 0:
    gc.collect()

# Limit cache size
CACHE_MAX_SIZE = 1000  # URLs
```

---

## Performance Tuning

### CPU Optimization
```bash
# Set CPU governor to performance
sudo cpupower frequency-set -g performance

# Disable CPU throttling
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Network Optimization
```bash
# Increase connection limits
sudo sysctl -w net.ipv4.ip_local_port_range="15000 65000"
sudo sysctl -w net.core.somaxconn=4096
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Enable TCP BBR
sudo sysctl -w net.core.default_qdisc=fq
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
```

### Disk I/O Optimization
```bash
# Use deadline scheduler for NVMe
echo deadline | sudo tee /sys/block/nvme0n1/queue/scheduler

# Increase readahead
sudo blockdev --setra 8192 /dev/nvme0n1
```

---

## Monitoring Requirements

### System Monitoring
```bash
# CPU, Memory, Disk every 5 minutes
*/5 * * * * top -bn1 | head -20 >> /var/log/system_stats.log

# Network bandwidth
*/5 * * * * vnstat -tr 5 >> /var/log/network_stats.log
```

### Application Monitoring
- Dashboard: Real-time metrics
- Email: Every 6 hours
- Health checks: Every 5 minutes
- Logs: Rotate daily

---

## Deployment Checklist

### Pre-deployment
- [ ] Server ordered and running
- [ ] Ubuntu 22.04 installed
- [ ] SSH access configured
- [ ] Firewall configured (ports 22, 8080)

### Installation
- [ ] Run `deployment/setup.sh`
- [ ] Configure `.env` with credentials
- [ ] Test email notifications
- [ ] Test proxy connection

### Optimization
- [ ] Set CPU governor to performance
- [ ] Apply network optimizations
- [ ] Configure disk scheduler
- [ ] Increase connection limits

### Start Scraping
- [ ] Start service: `systemctl start mrosupply-scraper`
- [ ] Verify in logs: First products scraping
- [ ] Check dashboard: Metrics updating
- [ ] Confirm email: Startup notification received

### Monitoring (First Hour)
- [ ] CPU usage: 60-80%
- [ ] Memory usage: 18-24 GB
- [ ] Network: 50-80 Mbps
- [ ] Success rate: >90%
- [ ] Speed: 17+ products/second

---

## Expected Timeline

### Hour 0-1 (Ramp-up)
- Workers starting: 0-50
- Speed ramping: 0 → 17 prod/s
- Products scraped: ~40,000

### Hour 1-12 (Steady state)
- Workers: 50 active
- Speed: 17-18 prod/s
- Products scraped: ~700,000

### Hour 12-20 (Late stage)
- Workers: 50 active
- Speed: 17-18 prod/s
- Products scraped: ~1,200,000

### Hour 20-24 (Completion)
- Workers: 40-50 active
- Speed: 15-18 prod/s
- Products scraped: 1,350,000-1,400,000

**Final:** 1,350,000+ products (90% of 1.5M) in 24 hours

---

## Troubleshooting

### If slower than expected:
1. Check CPU usage: Should be 60-80%
2. Check network: Should be 50-100 Mbps
3. Check success rate: Should be >90%
4. Increase workers: Try 60-70
5. Reduce delay: Try 0.15s

### If memory issues:
1. Reduce workers: Try 40
2. Enable aggressive GC
3. Clear cache more frequently
4. Restart service hourly (optional)

### If rate limited:
1. Adaptive rate will handle automatically
2. Check cooldown working
3. Verify proxy rotating
4. May need premium proxy plan

---

## Cost Breakdown (Complete)

| Item | Cost |
|------|------|
| Server (Hetzner 1 day) | $1.50 |
| Proxy (Webshare 75GB) | $25.00 |
| **Total** | **$26.50** |

Plus: One-time server setup (5 min)

**Cost per product: $0.0000177 (1.7 cents per 1000 products)**

---

## Summary

**Recommended Setup:**
- Server: Hetzner CCX32 (8 cores, 32GB, NVMe)
- Proxy: Webshare Premium Residential
- Workers: 50
- Delay: 0.2s
- **Time: 24 hours**
- **Cost: $26.50**
- **Success: 90%+ (1.35M products)**

Ready to deploy with `deployment/setup.sh`!
