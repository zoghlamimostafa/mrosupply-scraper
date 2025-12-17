#!/usr/bin/env python3
"""
Quick test of Fresh Proxy List for mrosupply.com scraping
Tests actual connection to the target website
"""

import requests
from proxy_manager import ProxyManager
import random
import time

def test_proxy_with_target(proxy_dict, test_url='https://www.mrosupply.com', timeout=10):
    """Test if proxy can access the target website"""
    try:
        proxy_url = list(proxy_dict.values())[0]
        response = requests.get(
            test_url,
            proxies=proxy_dict,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        )
        return response.status_code == 200, proxy_url, response.status_code
    except Exception as e:
        return False, list(proxy_dict.values())[0], str(e)

def main():
    print("="*70)
    print("FRESH PROXY LIST - TARGET WEBSITE TEST")
    print("="*70)
    print("Testing proxies against: https://www.mrosupply.com")
    print("="*70)
    
    # Load fresh proxies
    pm = ProxyManager(use_fresh_list=True)
    count = pm.fetch_proxies()
    print(f"\n✅ Loaded {count:,} proxies from Fresh List")
    
    # Test random sample
    sample_size = min(20, len(pm.proxies))
    sample = random.sample(pm.proxies, sample_size)
    
    print(f"\n🔍 Testing {sample_size} random proxies...")
    print("-"*70)
    
    working = []
    failed = []
    
    for i, proxy in enumerate(sample, 1):
        success, proxy_url, result = test_proxy_with_target(proxy)
        status = "✅" if success else "❌"
        print(f"{i:2d}. {status} {proxy_url[:50]:50s} {result}")
        
        if success:
            working.append(proxy)
        else:
            failed.append(proxy)
        
        time.sleep(0.5)  # Small delay between tests
    
    # Results
    print("="*70)
    print("TEST RESULTS:")
    print("="*70)
    print(f"✅ Working: {len(working)}/{sample_size} ({len(working)/sample_size*100:.1f}%)")
    print(f"❌ Failed:  {len(failed)}/{sample_size} ({len(failed)/sample_size*100:.1f}%)")
    print("="*70)
    
    if working:
        print(f"\n💡 {len(working)} proxies successfully connected to mrosupply.com")
        print(f"   Estimated working proxies from full list: ~{int(len(working)/sample_size * count):,}")
    else:
        print("\n⚠️  No working proxies found in sample")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
