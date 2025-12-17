#!/usr/bin/env python3
"""
Test Proxifly proxies (SOCKS4, SOCKS5, US proxies)
Tests actual connection to mrosupply.com
"""

import requests
import random
import time
from pathlib import Path

def load_proxies_from_file(filename):
    """Load proxies from file"""
    proxies = []
    if Path(filename).exists():
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
    return proxies

def test_proxy(proxy_url, test_url='https://www.mrosupply.com', timeout=30, retries=2):
    """Test if proxy can access the target website with retries"""
    for attempt in range(retries):
        try:
            # Determine protocol
            if proxy_url.startswith('socks5://'):
                proxy_dict = {
                    'http': proxy_url,
                    'https': proxy_url
                }
            elif proxy_url.startswith('socks4://'):
                proxy_dict = {
                    'http': proxy_url,
                    'https': proxy_url
                }
            else:
                # Assume http
                proxy_dict = {
                    'http': proxy_url,
                    'https': proxy_url
                }
            
            response = requests.get(
                test_url,
                proxies=proxy_dict,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
            )
            return True, response.status_code, len(response.content)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
                continue
            return False, str(e)[:80], 0
    
    return False, "Max retries exceeded", 0

def test_proxy_list(name, filename, sample_size=20, timeout=30, wait_time=1.0):
    """Test a proxy list with longer timeouts"""
    print(f"\n{'='*70}")
    print(f"TESTING: {name}")
    print(f"{'='*70}")
    
    proxies = load_proxies_from_file(filename)
    if not proxies:
        print(f"❌ No proxies found in {filename}")
        return 0, 0
    
    print(f"📊 Total proxies in file: {len(proxies)}")
    print(f"⏱️  Timeout: {timeout}s | Wait between tests: {wait_time}s | Retries: 2")
    
    # Test random sample
    sample = random.sample(proxies, min(sample_size, len(proxies)))
    print(f"🔍 Testing {len(sample)} random proxies...")
    print("-"*70)
    
    working = 0
    failed = 0
    
    for i, proxy in enumerate(sample, 1):
        result = test_proxy(proxy, timeout=timeout, retries=2)
        if result[0]:
            print(f"{i:2d}. ✅ {proxy:50s} Status: {result[1]} Size: {result[2]:,}b")
            working += 1
        else:
            print(f"{i:2d}. ❌ {proxy:50s} {result[1]}")
            failed += 1
        
        time.sleep(wait_time)  # Configurable delay
    
    success_rate = (working / len(sample) * 100) if sample else 0
    print("-"*70)
    print(f"✅ Working: {working}/{len(sample)} ({success_rate:.1f}%)")
    print(f"❌ Failed:  {failed}/{len(sample)} ({100-success_rate:.1f}%)")
    
    if working > 0:
        estimated_working = int(len(proxies) * (working / len(sample)))
        print(f"📈 Estimated working proxies: ~{estimated_working:,} out of {len(proxies):,}")
    
    return working, len(sample)
def main():
    print("="*70)
    print("PROXIFLY PROXY TEST - mrosupply.com (Extended Timeout)")
    print("="*70)
    print("Source: https://github.com/proxifly/free-proxy-list")
    print("Testing with: 30s timeout, 2 retries, 1s wait between tests")
    print("="*70)
    
    # Test each proxy list with longer timeout and wait
    results = []
    
    # SOCKS4 - slower, needs more time
    w, t = test_proxy_list("SOCKS4 Proxies", "socks4.txt", sample_size=20, timeout=30, wait_time=1.5)
    results.append(("SOCKS4", w, t))
    
    # SOCKS5 - generally faster than SOCKS4
    w, t = test_proxy_list("SOCKS5 Proxies", "socks5.txt", sample_size=20, timeout=25, wait_time=1.0)
    results.append(("SOCKS5", w, t))
    
    # U.S. Proxies - mixed types
    w, t = test_proxy_list("U.S. Proxies", "us_proxies.txt", sample_size=20, timeout=30, wait_time=1.5)
    results.append(("U.S. Proxies", w, t))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    for name, working, total in results:
        success_rate = (working / total * 100) if total > 0 else 0
        status = "✅" if working > 0 else "❌"
        print(f"{status} {name:20s}: {working:2d}/{total:2d} working ({success_rate:5.1f}%)")
    print("="*70)
    
    total_working = sum(r[1] for r in results)
    total_tested = sum(r[2] for r in results)
    overall_rate = (total_working / total_tested * 100) if total_tested > 0 else 0
    
    print(f"\n📊 Overall: {total_working}/{total_tested} working ({overall_rate:.1f}%)")
    
    if total_working > 0:
        print(f"✅ Found {total_working} working proxies!")
        print("💡 These SOCKS proxies support HTTPS and can scrape mrosupply.com")
    else:
        print("⚠️  No working proxies found")
        print("💡 Consider using Webshare paid proxies for reliable scraping")
    
    print("="*70)

if __name__ == "__main__":
    main()
