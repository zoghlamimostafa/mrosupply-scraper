jsut# 10 Proxy Performance Test Plan

## Your Proxy List

```
142.111.48.253:7030:yopfgyku:pn4xri0h48sy
31.59.20.176:6754:yopfgyku:pn4xri0h48sy
23.95.150.145:6114:yopfgyku:pn4xri0h48sy
198.23.239.134:6540:yopfgyku:pn4xri0h48sy
107.172.163.27:6543:yopfgyku:pn4xri0h48sy
198.105.121.200:6462:yopfgyku:pn4xri0h48sy
64.137.96.74:6641:yopfgyku:pn4xri0h48sy
84.247.60.125:6095:yopfgyku:pn4xri0h48sy
216.10.27.159:6837:yopfgyku:pn4xri0h48sy
142.111.67.146:5611:yopfgyku:pn4xri0h48sy
```

**Format:** IP:PORT:USERNAME:PASSWORD
**Count:** 10 proxies
**Type:** Appears to be residential or datacenter proxies
**Provider:** Unknown (possibly Webshare, IPRoyal, or similar)

---

## Test Objectives

### Primary Goals:
1. **Measure requests per proxy before ban**
2. **Calculate total capacity with 10 proxies**
3. **Determine cost per 1,000 products**
4. **Estimate time for 1.5M products**
5. **Find optimal rotation strategy**

### Secondary Goals:
- Test different request speeds
- Measure success rate over time
- Identify ban patterns
- Calculate bandwidth usage
- Compare to direct connection

---

## Testing Strategy

### Phase 1: Individual Proxy Testing (2-4 hours)

**Test each proxy individually to find ban threshold**

#### Test Parameters:
```bash
# Test 1: Single proxy, slow speed
Proxy: One at a time
Workers: 1
Delay: 2.0 seconds
Target: 100 products per proxy
Goal: Establish baseline

# Test 2: Single proxy, medium speed
Proxy: One at a time
Workers: 2
Delay: 1.0 seconds
Target: 200 products per proxy
Goal: Find breaking point

# Test 3: Single proxy, fast speed
Proxy: One at a time
Workers: 3
Delay: 0.5 seconds
Target: Until banned
Goal: Measure maximum capacity
```

#### Expected Results Per Proxy:
```
Scenario A (Conservative): 500-1,000 requests before ban
Scenario B (Moderate): 200-500 requests before ban
Scenario C (Aggressive): 50-200 requests before ban
```

### Phase 2: Rotation Testing (2-4 hours)

**Test rotating through all 10 proxies**

#### Rotation Strategies:

**Strategy 1: Round-robin (Sequential)**
```python
# Use proxy 1, then proxy 2, then proxy 3... then back to 1
Rotation: After each request
Workers: 10 (1 per proxy)
Delay: 1.0 seconds
Target: 1,000 products
Expected: High success rate
```

**Strategy 2: Random rotation**
```python
# Pick random proxy for each request
Rotation: Random selection
Workers: 10
Delay: 1.0 seconds
Target: 1,000 products
Expected: Medium success rate
```

**Strategy 3: Load-based rotation**
```python
# Rotate after N requests per proxy
Rotation: After 10-20 requests per proxy
Workers: 10
Delay: 0.5 seconds
Target: 1,000 products
Expected: Balanced load
```

### Phase 3: Stress Testing (4-8 hours)

**Push proxies to limits to find maximum capacity**

#### Stress Test Parameters:
```bash
# Aggressive test
Proxies: All 10 rotating
Workers: 50 (5 per proxy)
Delay: 0.3 seconds
Target: Until 50% failure rate
Goal: Find absolute maximum
```

#### Metrics to Track:
- Requests per proxy before first failure
- Success rate over time
- Response time degradation
- Ban recovery time (if any)
- Total products before collapse

### Phase 4: Production Simulation (8-24 hours)

**Simulate real scraping with optimal settings**

#### Production Test:
```bash
# Based on Phase 1-3 findings, use optimal settings
Proxies: All 10 with smart rotation
Workers: Optimal (determined from tests)
Delay: Optimal (determined from tests)
Target: 10,000-50,000 products
Goal: Validate long-term stability
```

---

## Detailed Test Plan

### Test 1: Single Proxy Capacity Test

**Goal:** Find how many requests each proxy can handle before ban

#### Setup:
```bash
# Create test configuration file
cat > test_single_proxy_config.json << EOF
{
  "test_name": "Single Proxy Capacity",
  "proxy": "142.111.48.253:7030:yopfgyku:pn4xri0h48sy",
  "workers": 1,
  "delay": 2.0,
  "max_products": 1000,
  "stop_on_ban": true,
  "track_metrics": true
}
EOF
```

#### Execution:
```bash
# Test each proxy one by one
for proxy in $(cat proxy_list.txt); do
    echo "Testing proxy: $proxy"
    python3 test_proxy_capacity.py \
        --proxy "$proxy" \
        --workers 1 \
        --delay 2.0 \
        --max-products 1000 \
        --output "results/proxy_${proxy%%:*}.json"

    echo "Waiting 5 minutes before next proxy..."
    sleep 300
done
```

#### Expected Output for Each Proxy:
```json
{
  "proxy": "142.111.48.253:7030",
  "test_start": "2025-12-15 10:00:00",
  "test_end": "2025-12-15 10:45:00",
  "total_requests": 847,
  "successful_requests": 823,
  "failed_requests": 24,
  "success_rate": 97.2,
  "avg_response_time": 1.2,
  "requests_before_first_failure": 312,
  "requests_before_ban": 823,
  "ban_detected": false,
  "rate_limited": false,
  "estimated_capacity": "800-1000 requests"
}
```

#### Analysis:
```
Best case per proxy: 800-1,000 successful requests
Worst case per proxy: 200-500 successful requests
Average case per proxy: 400-700 successful requests

With 10 proxies:
- Best case total: 8,000-10,000 requests
- Worst case total: 2,000-5,000 requests
- Average case total: 4,000-7,000 requests
```

### Test 2: Rotation Strategy Test

**Goal:** Find optimal proxy rotation strategy

#### Test 2A: Round-Robin Rotation
```bash
python3 test_rotation.py \
    --proxies proxy_list.txt \
    --strategy round-robin \
    --workers 10 \
    --delay 1.0 \
    --max-products 5000 \
    --output results/round_robin.json
```

**Expected behavior:**
- Each proxy gets equal load
- 1 request per proxy per 10 requests
- 500 requests per proxy for 5,000 products

**Expected results:**
```
Success rate: 85-95%
Failed requests: 250-750
Reason: Some proxies may be blocked, others working
Time: 1.5-2 hours
```

#### Test 2B: Random Rotation
```bash
python3 test_rotation.py \
    --proxies proxy_list.txt \
    --strategy random \
    --workers 10 \
    --delay 1.0 \
    --max-products 5000 \
    --output results/random.json
```

**Expected behavior:**
- Uneven load distribution
- Some proxies may get 600 requests, others 400
- Luck-based performance

**Expected results:**
```
Success rate: 80-90%
Failed requests: 500-1,000
Reason: Some proxies overused, some underused
Time: 1.5-2 hours
```

#### Test 2C: Smart Rotation (Weighted by Success)
```bash
python3 test_rotation.py \
    --proxies proxy_list.txt \
    --strategy smart \
    --workers 10 \
    --delay 1.0 \
    --max-products 5000 \
    --output results/smart.json
```

**Expected behavior:**
- Proxies with higher success rates get more requests
- Failed proxies are temporarily disabled
- Dynamic adjustment

**Expected results:**
```
Success rate: 90-96%
Failed requests: 200-500
Reason: Poor proxies disabled, good ones prioritized
Time: 1.5-2 hours
```

### Test 3: Speed vs Success Rate Test

**Goal:** Find optimal speed for maximum throughput

#### Speed Test Matrix:

| Test | Workers | Delay | Speed (req/sec) | Expected Success |
|------|---------|-------|-----------------|------------------|
| A | 10 | 3.0s | 3.3 | 95-100% ✅ |
| B | 10 | 2.0s | 5.0 | 90-95% ✅ |
| C | 10 | 1.0s | 10.0 | 80-90% ⚠️ |
| D | 20 | 1.0s | 20.0 | 70-80% ⚠️ |
| E | 30 | 0.5s | 60.0 | 40-60% ❌ |

#### Execution:
```bash
# Run each speed test
for test in A B C D E; do
    python3 test_speed.py \
        --test-config "configs/speed_test_${test}.json" \
        --max-products 1000 \
        --output "results/speed_test_${test}.json"

    echo "Waiting 10 minutes between tests..."
    sleep 600
done
```

#### Analysis:
```
Optimal speed = Maximum throughput with >85% success rate

If Test B (5 req/sec) achieves 90%+ success:
- Use 10 workers, 2.0s delay
- Speed: 5 products/second
- For 1.5M products: ~83 hours (3.5 days)

If Test C (10 req/sec) achieves 85%+ success:
- Use 10 workers, 1.0s delay
- Speed: 10 products/second
- For 1.5M products: ~42 hours (1.75 days)
```

### Test 4: Long-Duration Stability Test

**Goal:** Verify proxies remain stable over extended period

#### Setup:
```bash
# 24-hour stability test
python3 stability_test.py \
    --proxies proxy_list.txt \
    --duration 86400 \
    --workers 10 \
    --delay 1.5 \
    --target-products 50000 \
    --output results/stability_24h.json
```

#### Metrics to Track:
```
Hour 0-6:   Success rate, avg response time
Hour 6-12:  Success rate, any degradation?
Hour 12-18: Success rate, proxy failures?
Hour 18-24: Success rate, still working?

Expected pattern:
- Hour 0-6:   95% success (fresh proxies)
- Hour 6-12:  92% success (slight degradation)
- Hour 12-18: 88% success (some proxies failing)
- Hour 18-24: 85% success (need proxy rotation)
```

#### Decision Points:
```
If success rate drops below 80%:
- Pause scraping
- Disable failed proxies
- Continue with working proxies
- Document failure patterns
```

---

## Calculation Models

### Model 1: Conservative Estimate

**Assumptions:**
- Each proxy: 500 successful requests before issues
- Total capacity: 10 proxies × 500 = 5,000 products
- Speed: 5 products/second with 90% success
- Need retries: 10% failure rate

**For 1,508,692 products:**
```
Proxy cycles needed: 1,508,692 / 5,000 = ~302 cycles
Time per cycle: 5,000 / 5 = 1,000 seconds = ~17 minutes
Recovery time: 30 minutes between cycles
Total time per cycle: 47 minutes

Total time: 302 cycles × 47 min = 14,194 minutes = 237 hours = 9.9 days

NOTE: This assumes proxies recover after rest period
If proxies don't recover: Need 302 sets of 10 proxies = 3,020 proxies total
```

**Verdict: NOT FEASIBLE with only 10 proxies if they ban permanently**

### Model 2: Moderate Estimate

**Assumptions:**
- Each proxy: 1,000 successful requests before ban
- Total capacity: 10 proxies × 1,000 = 10,000 products
- Speed: 8 products/second with 85% success
- Proxies can recover with rest

**For 1,508,692 products:**
```
Effective products per cycle: 10,000 × 0.85 = 8,500
Cycles needed: 1,508,692 / 8,500 = ~178 cycles
Time per cycle: 10,000 / 8 = 1,250 seconds = ~21 minutes
Recovery time: 1 hour between cycles
Total time per cycle: 81 minutes

Total time: 178 cycles × 81 min = 14,418 minutes = 240 hours = 10 days

If proxies recover: POSSIBLE but SLOW (10 days)
If proxies don't recover: Need 178 sets = 1,780 proxies
```

### Model 3: Optimistic Estimate

**Assumptions:**
- Each proxy: 2,000 successful requests before temporary rate limit
- Total capacity: 10 proxies × 2,000 = 20,000 products
- Speed: 10 products/second with 90% success
- Proxies recover after 30 minutes rest

**For 1,508,692 products:**
```
Effective products per cycle: 20,000 × 0.90 = 18,000
Cycles needed: 1,508,692 / 18,000 = ~84 cycles
Time per cycle: 20,000 / 10 = 2,000 seconds = ~33 minutes
Recovery time: 30 minutes between cycles
Total time per cycle: 63 minutes

Total time: 84 cycles × 63 min = 5,292 minutes = 88 hours = 3.7 days

If proxies recover: FEASIBLE (3.7 days)
If proxies don't recover: Need 84 sets = 840 proxies
```

### Model 4: Real-World Estimate (Most Likely)

**Based on your test results from documentation:**
- Free proxies: 0% success (IP blocked)
- Direct connection: 100% success at 1/sec

**For your 10 proxies:**
```
Best case scenario:
- These are residential proxies (not free/datacenter)
- Each can handle 500-1,000 requests
- Can be reused after cooldown
- 80-85% success rate

Calculation:
Products per proxy cycle: 500 (conservative)
Total per cycle (10 proxies): 5,000
With 85% success: 4,250 effective products
Cycles needed: 1,508,692 / 4,250 = 355 cycles
Time per cycle: 5,000 / 5 = 1,000 sec = 17 min
Cooldown: 1-2 hours
Total per cycle: 77-137 minutes (avg 107 min)

Total time: 355 × 107 min = 37,985 min = 633 hours = 26.4 days

VERDICT: 26-27 days with 10 proxies (if they recover)
```

---

## Testing Commands

### Test Command 1: Basic Connectivity Test
```bash
# Test if all proxies connect to mrosupply.com
python3 << 'EOF'
import requests

proxies_list = [
    "142.111.48.253:7030:yopfgyku:pn4xri0h48sy",
    "31.59.20.176:6754:yopfgyku:pn4xri0h48sy",
    "23.95.150.145:6114:yopfgyku:pn4xri0h48sy",
    "198.23.239.134:6540:yopfgyku:pn4xri0h48sy",
    "107.172.163.27:6543:yopfgyku:pn4xri0h48sy",
    "198.105.121.200:6462:yopfgyku:pn4xri0h48sy",
    "64.137.96.74:6641:yopfgyku:pn4xri0h48sy",
    "84.247.60.125:6095:yopfgyku:pn4xri0h48sy",
    "216.10.27.159:6837:yopfgyku:pn4xri0h48sy",
    "142.111.67.146:5611:yopfgyku:pn4xri0h48sy"
]

test_url = "https://www.mrosupply.com"
working = []
failed = []

for proxy_str in proxies_list:
    parts = proxy_str.split(':')
    ip, port, username, password = parts[0], parts[1], parts[2], parts[3]

    proxy_url = f"http://{username}:{password}@{ip}:{port}"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }

    try:
        response = requests.get(test_url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"✅ {ip}:{port} - Working (Status: {response.status_code})")
            working.append(proxy_str)
        else:
            print(f"⚠️ {ip}:{port} - Status: {response.status_code}")
            failed.append(proxy_str)
    except Exception as e:
        print(f"❌ {ip}:{port} - Failed: {str(e)[:50]}")
        failed.append(proxy_str)

print(f"\n{'='*60}")
print(f"Working proxies: {len(working)}/10")
print(f"Failed proxies: {len(failed)}/10")
print(f"Success rate: {len(working)*10}%")
EOF
```

**Expected output:**
```
✅ 142.111.48.253:7030 - Working (Status: 200)
✅ 31.59.20.176:6754 - Working (Status: 200)
...
============================================================
Working proxies: 8-10/10
Failed proxies: 0-2/10
Success rate: 80-100%
```

### Test Command 2: Single Proxy Load Test
```bash
# Test how many requests one proxy can handle
python3 << 'EOF'
import requests
import time

proxy_str = "142.111.48.253:7030:yopfgyku:pn4xri0h48sy"
parts = proxy_str.split(':')
ip, port, username, password = parts[0], parts[1], parts[2], parts[3]

proxy_url = f"http://{username}:{password}@{ip}:{port}"
proxies = {'http': proxy_url, 'https': proxy_url}

test_url = "https://www.mrosupply.com/hydraulics-and-pneumatics/hose-pipe-tube-fittings/rotary-unions/deublin/755-702-413139/"

success_count = 0
fail_count = 0
request_count = 0
start_time = time.time()

print(f"Testing proxy: {ip}:{port}")
print(f"Target: 100 requests with 1 second delay")
print(f"{'='*60}\n")

for i in range(100):
    request_count += 1
    try:
        response = requests.get(test_url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            success_count += 1
            print(f"Request {request_count}: ✅ Success (Total: {success_count}/{request_count})")
        else:
            fail_count += 1
            print(f"Request {request_count}: ⚠️ Status {response.status_code} (Fails: {fail_count})")
    except Exception as e:
        fail_count += 1
        print(f"Request {request_count}: ❌ Error (Fails: {fail_count})")

        # If 3 consecutive failures, stop
        if fail_count >= 3 and success_count == 0:
            print(f"\n❌ Proxy appears to be blocked. Stopping test.")
            break

    time.sleep(1)  # 1 second delay

    # Progress update every 10 requests
    if request_count % 10 == 0:
        success_rate = (success_count / request_count) * 100
        print(f"\n--- Progress: {request_count}/100 | Success: {success_rate:.1f}% ---\n")

end_time = time.time()
total_time = end_time - start_time
success_rate = (success_count / request_count) * 100

print(f"\n{'='*60}")
print(f"RESULTS:")
print(f"Total requests: {request_count}")
print(f"Successful: {success_count}")
print(f"Failed: {fail_count}")
print(f"Success rate: {success_rate:.1f}%")
print(f"Total time: {total_time/60:.1f} minutes")
print(f"Avg time per request: {total_time/request_count:.2f} seconds")
print(f"{'='*60}")

if success_rate > 90:
    print(f"✅ Proxy is WORKING WELL")
elif success_rate > 70:
    print(f"⚠️ Proxy is WORKING but with issues")
else:
    print(f"❌ Proxy is BLOCKED or NOT WORKING")
EOF
```

### Test Command 3: All Proxies Rotation Test
```bash
# Test rotating through all 10 proxies
python3 << 'EOF'
import requests
import time
import random

proxies_list = [
    "142.111.48.253:7030:yopfgyku:pn4xri0h48sy",
    "31.59.20.176:6754:yopfgyku:pn4xri0h48sy",
    "23.95.150.145:6114:yopfgyku:pn4xri0h48sy",
    "198.23.239.134:6540:yopfgyku:pn4xri0h48sy",
    "107.172.163.27:6543:yopfgyku:pn4xri0h48sy",
    "198.105.121.200:6462:yopfgyku:pn4xri0h48sy",
    "64.137.96.74:6641:yopfgyku:pn4xri0h48sy",
    "84.247.60.125:6095:yopfgyku:pn4xri0h48sy",
    "216.10.27.159:6837:yopfgyku:pn4xri0h48sy",
    "142.111.67.146:5611:yopfgyku:pn4xri0h48sy"
]

def get_proxy_dict(proxy_str):
    parts = proxy_str.split(':')
    ip, port, username, password = parts[0], parts[1], parts[2], parts[3]
    proxy_url = f"http://{username}:{password}@{ip}:{port}"
    return {'http': proxy_url, 'https': proxy_url}, f"{ip}:{port}"

test_url = "https://www.mrosupply.com/hydraulics-and-pneumatics/hose-pipe-tube-fittings/rotary-unions/deublin/755-702-413139/"

total_requests = 50  # 5 requests per proxy
success_count = 0
fail_count = 0
proxy_stats = {p.split(':')[0]: {'success': 0, 'fail': 0} for p in proxies_list}

print(f"Testing rotation through 10 proxies")
print(f"Total requests: {total_requests} ({total_requests//10} per proxy)")
print(f"{'='*60}\n")

start_time = time.time()

for i in range(total_requests):
    # Round-robin: cycle through proxies
    proxy_str = proxies_list[i % len(proxies_list)]
    proxies, proxy_display = get_proxy_dict(proxy_str)
    proxy_ip = proxy_str.split(':')[0]

    try:
        response = requests.get(test_url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            success_count += 1
            proxy_stats[proxy_ip]['success'] += 1
            status = "✅"
        else:
            fail_count += 1
            proxy_stats[proxy_ip]['fail'] += 1
            status = f"⚠️ {response.status_code}"
    except Exception as e:
        fail_count += 1
        proxy_stats[proxy_ip]['fail'] += 1
        status = "❌"

    print(f"Request {i+1}: {proxy_display} {status} (Success: {success_count}/{i+1})")
    time.sleep(0.5)  # 0.5 second delay

end_time = time.time()
total_time = end_time - start_time
success_rate = (success_count / total_requests) * 100

print(f"\n{'='*60}")
print(f"OVERALL RESULTS:")
print(f"Total requests: {total_requests}")
print(f"Successful: {success_count}")
print(f"Failed: {fail_count}")
print(f"Success rate: {success_rate:.1f}%")
print(f"Total time: {total_time:.1f} seconds")
print(f"{'='*60}\n")

print(f"PER-PROXY RESULTS:")
for proxy_str in proxies_list:
    proxy_ip = proxy_str.split(':')[0]
    stats = proxy_stats[proxy_ip]
    total = stats['success'] + stats['fail']
    rate = (stats['success'] / total * 100) if total > 0 else 0
    print(f"{proxy_ip}: {stats['success']}/{total} ({rate:.0f}%)")

print(f"{'='*60}")
EOF
```

---

## Expected Test Results

### Scenario A: Best Case (Residential Proxies, Good Quality)
```
Single proxy capacity: 1,000-2,000 requests
Total capacity (10 proxies): 10,000-20,000 requests
Success rate: 90-95%
Speed: 8-10 products/second
Estimated time for 1.5M: 3-5 days
Cost: Already paid for proxies
```

### Scenario B: Medium Case (Mixed Quality)
```
Single proxy capacity: 500-1,000 requests
Total capacity (10 proxies): 5,000-10,000 requests
Success rate: 80-90%
Speed: 5-8 products/second
Estimated time for 1.5M: 7-14 days
Cost: Already paid for proxies
```

### Scenario C: Worst Case (Datacenter IPs, Already Known)
```
Single proxy capacity: 50-200 requests
Total capacity (10 proxies): 500-2,000 requests
Success rate: 30-60%
Speed: 2-4 products/second with high failure
Estimated time for 1.5M: 30-60 days (with many retry cycles)
Cost: Already paid for proxies + time wasted
```

### Scenario D: Blocked (Like Free Proxies)
```
Single proxy capacity: 0-10 requests
Total capacity (10 proxies): 0-100 requests
Success rate: 0-10%
Speed: N/A
Estimated time for 1.5M: IMPOSSIBLE
Cost: Wasted money on proxies
```

---

## Cost Analysis

### Cost Calculation Models:

#### Model 1: Proxies Already Paid For
```
If these 10 proxies were purchased:
- Typical cost: $5-20 per proxy per month
- Total paid: $50-200 for the set

Sunk cost: Already paid
Additional cost: $0 (just server/electricity)

Cost per product: $0 (ignoring sunk cost)
Or: $50-200 / 1,508,692 = $0.000033-0.000133 per product
```

#### Model 2: Server Costs
```
If running on AWS/VPS:
- Small VPS: $10-40/month
- AWS instance: $0.05-0.30/hour

For 3-5 day run:
- VPS: $10-40 (monthly, can reuse)
- AWS: $3.60-36 (72-120 hours × rate)

Cost per product: $0.000002-0.000024
```

#### Model 3: Bandwidth Costs
```
Estimated bandwidth: 180-220 GB
If paying for bandwidth: $0-10 (most home/VPS have unlimited)

Cost per product: $0-0.000007
```

#### Model 4: Total Effective Cost
```
Proxies (if buying new): $50-200
Server (3-5 days): $10-40
Bandwidth: $0-10
Total: $60-250

Cost per product: $0.00004-0.00017

For comparison:
- Free direct connection: $0
- Webshare residential: $0.00048 per product
- Your 10 proxies: $0.00004-0.00017 (much cheaper!)
```

---

## Performance Calculations

### Calculation 1: Maximum Theoretical Speed

**Assumptions:**
- 10 proxies working simultaneously
- No rate limiting
- 100% success rate
- Instant response

**Calculation:**
```
Workers: 10 (one per proxy)
Delay: 0 seconds (theoretical)
Speed: 10 requests/second

For 1,508,692 products:
Time = 1,508,692 / 10 = 150,869 seconds = 2,514 minutes = 41.9 hours

THEORETICAL MINIMUM: 42 hours (1.75 days)
```

**Reality: IMPOSSIBLE**
- Will hit rate limits
- Will get banned
- Success rate will drop to 0%

### Calculation 2: Aggressive Realistic Speed

**Assumptions:**
- 10 proxies, rotating
- Workers: 20 (2 per proxy)
- Delay: 0.5 seconds
- Success rate: 70%

**Calculation:**
```
Effective speed: 20 / 0.5 = 40 requests/second
With 70% success: 28 products/second

For 1,508,692 products:
Time = 1,508,692 / 28 = 53,882 seconds = 898 minutes = 15 hours

With retries for 30% failures:
Additional time: 452,608 products / 28 = 16,165 seconds = 4.5 hours
Total: 19.5 hours

AGGRESSIVE REALISTIC: 20 hours (<1 day)
```

**Risk: HIGH**
- May burn proxies fast
- Success rate may be lower
- May need multiple proxy sets

### Calculation 3: Balanced Realistic Speed

**Assumptions:**
- 10 proxies, rotating
- Workers: 10 (1 per proxy)
- Delay: 1.5 seconds
- Success rate: 85%

**Calculation:**
```
Effective speed: 10 / 1.5 = 6.67 requests/second
With 85% success: 5.67 products/second

For 1,508,692 products:
Time = 1,508,692 / 5.67 = 266,102 seconds = 4,435 minutes = 73.9 hours = 3.1 days

With retries for 15% failures:
Additional time: 226,304 products / 5.67 = 39,929 seconds = 11.1 hours
Total: 85 hours = 3.5 days

BALANCED REALISTIC: 3.5 days
```

**Risk: MEDIUM**
- Good balance
- Proxies should last
- High success rate

### Calculation 4: Conservative Realistic Speed

**Assumptions:**
- 10 proxies, rotating carefully
- Workers: 10 (1 per proxy)
- Delay: 2.5 seconds
- Success rate: 92%

**Calculation:**
```
Effective speed: 10 / 2.5 = 4 requests/second
With 92% success: 3.68 products/second

For 1,508,692 products:
Time = 1,508,692 / 3.68 = 409,999 seconds = 6,833 minutes = 113.9 hours = 4.7 days

With retries for 8% failures:
Additional time: 120,695 products / 3.68 = 32,799 seconds = 9.1 hours
Total: 123 hours = 5.1 days

CONSERVATIVE REALISTIC: 5 days
```

**Risk: LOW**
- Safest approach
- Proxies should last entire run
- Minimal failures

---

## Estimated Timeline for 1.5M Products

### Summary Table:

| Scenario | Workers | Delay | Speed | Success Rate | Time | Risk |
|----------|---------|-------|-------|--------------|------|------|
| Theoretical Max | 10 | 0s | 10/s | 100% | 42h (1.75 days) | IMPOSSIBLE ❌ |
| Aggressive | 20 | 0.5s | 28/s effective | 70% | 20h (<1 day) | HIGH ⚠️⚠️⚠️ |
| Balanced | 10 | 1.5s | 5.67/s effective | 85% | 85h (3.5 days) | MEDIUM ⚠️ |
| Conservative | 10 | 2.5s | 3.68/s effective | 92% | 123h (5 days) | LOW ✅ |
| Ultra-Safe | 5 | 3.0s | 1.53/s effective | 95% | 273h (11 days) | VERY LOW ✅✅ |

---

## Recommended Testing Schedule

### Day 1: Initial Testing (4-6 hours)
```
Hour 0-1: Connectivity test (Test Command 1)
- Test all 10 proxies
- Identify working proxies
- Disable dead proxies

Hour 1-2: Single proxy capacity test (Test Command 2)
- Test one proxy until failure
- Measure capacity
- Determine if proxies are residential or datacenter

Hour 2-4: Rotation test (Test Command 3)
- Test all working proxies in rotation
- Measure success rate
- Find optimal rotation strategy

Hour 4-6: Speed test
- Test different speeds (slow, medium, fast)
- Find optimal speed for 85%+ success
- Document findings
```

### Day 2: Extended Testing (8-12 hours)
```
Hour 0-4: Medium-scale test
- Target: 5,000-10,000 products
- Use optimal settings from Day 1
- Monitor success rate
- Track proxy performance

Hour 4-8: Adjust and retry
- If issues found, adjust settings
- Disable problematic proxies
- Re-test with refined settings

Hour 8-12: Validation test
- Another 5,000-10,000 products
- Confirm stability
- Calculate final estimates
```

### Day 3: Decision Point
```
Based on Day 1-2 results:

If success rate >85% and proxies stable:
→ Proceed to production (3-5 day run)

If success rate 70-85%:
→ Proceed with caution (5-7 day run)
→ Have retry strategy ready

If success rate <70%:
→ Stop, proxies are not good enough
→ Consider alternatives (direct connection, better proxies)
```

### Days 4-8: Production Run (if tests passed)
```
Run full scraping with optimal settings
Monitor continuously
Adjust if needed
Complete 1.5M products
```

---

## Success Criteria

### Minimum Viable Results:
- ✅ At least 7/10 proxies working
- ✅ Success rate >80%
- ✅ Can complete 1,000 products with <20% failure
- ✅ Proxies last for 500+ requests each
- ✅ Total time <7 days

### Good Results:
- ✅ 9-10/10 proxies working
- ✅ Success rate >85%
- ✅ Can complete 1,000 products with <15% failure
- ✅ Proxies last for 1,000+ requests each
- ✅ Total time 3-5 days

### Excellent Results:
- ✅ 10/10 proxies working
- ✅ Success rate >90%
- ✅ Can complete 1,000 products with <10% failure
- ✅ Proxies last for 2,000+ requests each
- ✅ Total time <3 days

---

## What to Track During Tests

### Metrics to Log:

1. **Per Request:**
   - Timestamp
   - Proxy used
   - Response status code
   - Response time
   - Success/failure
   - Error message (if any)

2. **Per Proxy:**
   - Total requests
   - Successful requests
   - Failed requests
   - Success rate
   - Average response time
   - First failure at request #
   - Banned (yes/no)

3. **Overall:**
   - Total time
   - Total requests
   - Total products scraped
   - Overall success rate
   - Average speed (products/second)
   - Bandwidth used
   - Proxies still working

### Output Format:
```json
{
  "test_name": "10 Proxy Capacity Test",
  "start_time": "2025-12-15 10:00:00",
  "end_time": "2025-12-15 13:45:30",
  "duration_hours": 3.76,
  "proxies_tested": 10,
  "proxies_working": 8,
  "total_requests": 12547,
  "successful_requests": 10865,
  "failed_requests": 1682,
  "overall_success_rate": 86.6,
  "products_scraped": 10865,
  "average_speed": 0.80,
  "estimated_bandwidth_mb": 1523,
  "proxy_details": [
    {
      "ip": "142.111.48.253",
      "port": 7030,
      "requests": 1255,
      "successful": 1198,
      "failed": 57,
      "success_rate": 95.5,
      "avg_response_time": 1.2,
      "status": "working"
    },
    ...
  ],
  "recommendations": {
    "optimal_workers": 10,
    "optimal_delay": 1.5,
    "expected_time_for_full_scrape": "3.5 days",
    "estimated_success_rate": "85-90%"
  }
}
```

---

## Final Recommendations

### Based on Documentation Review:

Your tests showed:
- Direct connection: 100% success ✅
- Free proxies: 0% success ❌

**Your 10 proxies will likely fall into one of these categories:**

**Category A: Residential Proxies (Best Case)**
- Success rate: 85-92%
- Time for 1.5M: 3-5 days
- **Recommendation: USE THEM** ⭐⭐⭐

**Category B: Quality Datacenter (Medium Case)**
- Success rate: 70-85%
- Time for 1.5M: 5-7 days
- **Recommendation: Use with caution** ⚠️

**Category C: Poor Quality (Like Free Proxies)**
- Success rate: 0-40%
- Time for 1.5M: IMPOSSIBLE
- **Recommendation: DON'T USE** ❌

### Testing Will Reveal:

Run the 3 test commands provided to determine which category your proxies fall into:

1. **Test Command 1** (5 min): Check if proxies connect
2. **Test Command 2** (2 hours): Check capacity of one proxy
3. **Test Command 3** (30 min): Check rotation performance

**After tests, you'll know:**
- Are these proxies worth using?
- How long will it take?
- What success rate to expect?

### Next Steps:

1. **Run connectivity test** (5 minutes)
2. **If 8+ proxies work:** Run capacity test
3. **If capacity >500 requests:** Run rotation test
4. **If success rate >80%:** Proceed to production
5. **If any test fails:** Fall back to free direct connection

---

## Cost Summary

### If Tests Show Proxies Are Good:

**Best Case (3-5 days):**
```
Proxy cost: $50-200 (already paid)
Server cost: $10-40 (VPS) or $15-60 (AWS)
Bandwidth: $0-10
Total: $60-250
Per product: $0.00004-0.00017
```

**Compared to alternatives:**
- Free direct (30-60 days): $0
- Webshare residential (4 days): $721
- **Your proxies (3-5 days): $60-250** ⭐ BEST VALUE

### If Tests Show Proxies Are Bad:

**Fall back to free option:**
```
Direct connection: $0
Time: 30-60 days
Success rate: 95-100%
```

---

## Conclusion

**Your 10 proxies could be a game-changer IF:**
- They're residential or high-quality datacenter IPs
- They're not already blocked by mrosupply.com
- They can handle 500-1,000+ requests each

**Run the tests to find out!**

**Testing schedule:**
- Day 1: Run all 3 test commands (6 hours)
- Day 2: Decide based on results
- Days 3-8: Production run (if tests passed)

**Expected outcome:**
- Best case: 3-5 days at $60-250 (excellent value!)
- Worst case: Proxies blocked, use free option (30-60 days at $0)

**The tests will tell you definitively which scenario you're in.**
