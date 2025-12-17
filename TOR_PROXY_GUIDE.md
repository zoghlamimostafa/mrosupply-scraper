# Using Tor as Free Proxy for Scraping

## Overview

**Tor** (The Onion Router) can be used as a **FREE proxy** alternative to expensive residential proxies. Perfect for scraping 1.5M products at $0 cost!

## ✅ Advantages

| Feature | Tor | Webshare Residential |
|---------|-----|---------------------|
| **Cost** | ✅ **FREE** | ❌ $4,200/month |
| **IP Rotation** | ✅ Every 10 minutes | ✅ Per request |
| **Bandwidth** | ✅ Unlimited | ❌ Limited (411 GB needed) |
| **Setup** | ⚠️ Moderate | ✅ Easy |
| **Speed** | ⚠️ Slower (2-5 sec) | ✅ Fast (<1 sec) |
| **Anonymity** | ✅ Excellent | ⚠️ Good |

## ⚠️ Disadvantages

- **Slower speeds** (Tor has latency)
- **May be blocked** (some sites block Tor exit nodes)
- **Need to rotate circuits** manually
- **Not suitable for high-speed scraping**

## 🚀 Setup Guide

### **1. Install Tor**

**On Ubuntu/Debian (your server):**
```bash
sudo apt update
sudo apt install tor -y
```

**On Mac:**
```bash
brew install tor
```

**On Windows:**
Download from: https://www.torproject.org/download/

### **2. Configure Tor**

Edit Tor config:
```bash
sudo nano /etc/tor/torrc
```

Add these lines:
```
# Enable SOCKS proxy on port 9050
SOCKSPort 9050

# Enable control port for IP rotation
ControlPort 9051

# Set control password
HashedControlPassword 16:872860B76453A77D60CA2BB8C1A7042072093276A3D701AD684053EC4C

# Allow connections from localhost
CookieAuthentication 0
```

**Generate your own password hash:**
```bash
tor --hash-password mypassword
# Copy the output and replace the HashedControlPassword line
```

### **3. Start Tor Service**

```bash
# Start Tor
sudo systemctl start tor

# Enable on boot
sudo systemctl enable tor

# Check status
sudo systemctl status tor
```

### **4. Test Tor Connection**

```bash
# Test SOCKS proxy
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip

# Should return a Tor exit node IP, not your real IP
```

## 📝 Python Implementation

### **Basic Tor Scraper**

```python
import requests
from stem import Signal
from stem.control import Controller

# Tor proxy settings
PROXIES = {
    'http': 'socks5://127.0.0.1:9050',
    'https': 'socks5://127.0.0.1:9050'
}

def get_tor_session():
    """Create session with Tor proxy"""
    session = requests.Session()
    session.proxies.update(PROXIES)
    return session

def renew_tor_ip():
    """Request new Tor circuit (new IP)"""
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='mypassword')
        controller.signal(Signal.NEWNYM)
    time.sleep(5)  # Wait for new circuit

# Usage
session = get_tor_session()
response = session.get('https://www.mrosupply.com/product/123')
```

## 🛠️ Complete Tor Scraper Script

I'll create a full scraper with Tor integration:

### **Features:**
- ✅ Uses Tor as free proxy
- ✅ Rotates IP every N requests
- ✅ Handles Tor connection failures
- ✅ Falls back to direct connection if Tor fails
- ✅ Works with existing sitemap scraper

### **Speed Optimization:**
- Multiple Tor instances on different ports
- Each worker uses different Tor circuit
- Can achieve 5-10 products/second with 10 Tor instances

## 💰 Cost Comparison

### **Scenario: 1.5M Products**

| Method | Setup Time | Scraping Time | Cost | Bandwidth |
|--------|-----------|---------------|------|-----------|
| **No Proxy** | 0 min | 15-20 days | $0 | Unlimited |
| **Single Tor** | 10 min | 20-25 days | $0 | Unlimited |
| **10 Tor Instances** | 30 min | 8-12 days | $0 | Unlimited |
| **Webshare Residential** | 5 min | 4-5 days | $4,200 | 411 GB |

## ⚡ Multi-Tor Setup (FASTER)

Run multiple Tor instances on different ports for parallel scraping:

### **Setup 10 Tor Instances:**

```bash
# Create config for each instance
for i in {1..10}; do
  PORT=$((9050 + i))
  CONTROL_PORT=$((9051 + i))

  sudo mkdir -p /var/lib/tor/instance$i
  sudo cat > /etc/tor/torrc.instance$i << EOF
SOCKSPort $PORT
ControlPort $CONTROL_PORT
DataDirectory /var/lib/tor/instance$i
EOF

  # Start instance
  tor -f /etc/tor/torrc.instance$i &
done
```

Now you have Tor proxies on ports: 9051-9060

## 🎯 Recommended Approach

### **Option 1: Start Simple (Single Tor)**
- Setup time: 10 minutes
- Speed: 2-3 products/second
- Time for 1.5M: ~20 days
- Cost: **FREE**

### **Option 2: Multi-Tor (Faster)**
- Setup time: 30 minutes
- Speed: 10-15 products/second
- Time for 1.5M: ~8-12 days
- Cost: **FREE**

### **Option 3: Hybrid (Tor + Direct)**
- Use Tor for some requests
- Use direct connection for others
- Rotate between them
- Best of both worlds

## 🚫 When NOT to Use Tor

❌ Don't use Tor if:
- Site actively blocks Tor exit nodes
- You need very fast scraping (<5 days)
- You're running commercial operation
- You need 99.9% uptime

✅ Use Tor if:
- You want FREE proxy solution
- Time is not critical (can wait 10-20 days)
- You want maximum anonymity
- Budget is tight

## 🔍 Testing Tor for mrosupply.com

Let's test if mrosupply.com blocks Tor:

```bash
# Test via Tor
curl --socks5 127.0.0.1:9050 https://www.mrosupply.com/

# If it works, you're good to go!
# If blocked, you'll get 403 or connection refused
```

## 📊 Real-World Performance

Based on typical Tor performance:

| Metric | Single Tor | 10 Tor Instances |
|--------|-----------|------------------|
| **Speed** | 2-3 req/sec | 15-20 req/sec |
| **Latency** | 3-5 seconds | 2-3 seconds |
| **Success Rate** | 85-90% | 90-95% |
| **Time for 1.5M** | 20-25 days | 8-12 days |

## 🎬 Next Steps

1. **Test Tor with 100 products first**
2. **Check if mrosupply.com blocks Tor**
3. **If works, scale to 10K products**
4. **If successful, run full 1.5M scrape**

## 💡 My Recommendation

**Try this progression:**

1. ✅ **First:** Test WITHOUT proxy (FREE, fastest setup)
2. ⚠️ **If blocked:** Try single Tor instance (FREE)
3. 🚀 **If Tor works:** Setup 10 Tor instances (FREE, faster)
4. 💰 **If Tor blocked:** Then consider paid proxies

This way you only spend money if absolutely necessary!

---

**Want me to create a Tor-integrated scraper script?**
