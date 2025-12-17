#!/usr/bin/env python3
"""
Proxy Manager with rotation and health checking
Fetches proxies from TheSpeedX/PROXY-List repository
"""

import random
import requests
from typing import List, Optional, Dict
from threading import Lock
from collections import defaultdict
import time


class ProxyManager:
    """Manages proxy rotation and health checking"""

    # GeoNode API endpoint (better than TheSpeedX - provides checked proxies)
    GEONODE_API = "https://proxylist.geonode.com/api/proxy-list"
    
    # Fresh Proxy List (updates every 5-20 minutes, ~89% success rate)
    FRESH_PROXY_URL = "https://vakhov.github.io/fresh-proxy-list/proxylist.txt"

    def __init__(self, proxy_types: List[str] = ['http', 'socks5'], test_url: str = 'https://www.mrosupply.com',
                 use_geonode: bool = True, use_fresh_list: bool = False):
        """
        Initialize proxy manager

        Args:
            proxy_types: Types of proxies to use ['http', 'socks4', 'socks5']
            test_url: URL to test proxies against
            use_geonode: Use GeoNode API (recommended) vs TheSpeedX lists
            use_fresh_list: Use Fresh Proxy List (89% success rate, updates every 5-20min)
        """
        self.proxy_types = proxy_types
        self.test_url = test_url
        self.use_geonode = use_geonode
        self.use_fresh_list = use_fresh_list
        self.proxies: List[Dict[str, str]] = []
        self.working_proxies: List[Dict[str, str]] = []
        self.failed_proxies: set = set()
        self.proxy_stats = defaultdict(lambda: {'success': 0, 'failed': 0})
        self.lock = Lock()
        self.current_index = 0

    def fetch_proxies_geonode(self, limit: int = 500, min_uptime: float = 50.0) -> int:
        """
        Fetch proxies from GeoNode API (recommended - provides checked proxies)

        Args:
            limit: Number of proxies to fetch per page
            min_uptime: Minimum uptime percentage (0-100)
        """
        print(f"Fetching proxies from GeoNode API...")
        all_proxies = []

        # Map protocol types
        protocol_map = {
            'http': ['http', 'https'],
            'socks4': ['socks4'],
            'socks5': ['socks5']
        }

        for proxy_type in self.proxy_types:
            if proxy_type not in protocol_map:
                print(f"Unknown proxy type: {proxy_type}")
                continue

            try:
                print(f"  Fetching {proxy_type} proxies...")

                # Build API URL with filters
                params = {
                    'limit': limit,
                    'page': 1,
                    'sort_by': 'lastChecked',
                    'sort_type': 'desc',
                    'protocols': ','.join(protocol_map[proxy_type])
                }

                response = requests.get(self.GEONODE_API, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                if 'data' not in data:
                    print(f"    No data in response")
                    continue

                proxies_data = data['data']
                count = 0

                for proxy in proxies_data:
                    # Filter by uptime
                    uptime = proxy.get('upTime', 0)
                    if uptime < min_uptime:
                        continue

                    ip = proxy.get('ip')
                    port = proxy.get('port')
                    protocols = proxy.get('protocols', [])

                    if not ip or not port:
                        continue

                    # Create proxy URL
                    protocol = protocols[0] if protocols else proxy_type
                    proxy_url = f"{protocol}://{ip}:{port}"

                    all_proxies.append({
                        'http': proxy_url,
                        'https': proxy_url,
                        'type': protocol,
                        'address': f"{ip}:{port}",
                        'uptime': uptime,
                        'latency': proxy.get('latency', 999),
                        'country': proxy.get('country', ''),
                        'anonymity': proxy.get('anonymityLevel', '')
                    })
                    count += 1

                print(f"    Loaded {count} {proxy_type} proxies (uptime >= {min_uptime}%)")

            except Exception as e:
                print(f"    Failed to fetch {proxy_type} proxies: {e}")

        # Sort by uptime (best first)
        all_proxies.sort(key=lambda x: x.get('uptime', 0), reverse=True)

        self.proxies = all_proxies
        print(f"\nTotal proxies loaded: {len(self.proxies)}")
        if all_proxies:
            avg_uptime = sum(p.get('uptime', 0) for p in all_proxies) / len(all_proxies)
            print(f"Average uptime: {avg_uptime:.1f}%")
        return len(self.proxies)

    def fetch_proxies_speedx(self) -> int:
        """
        Legacy method: Fetch proxies from TheSpeedX/PROXY-List
        Not recommended - use GeoNode instead (use_geonode=True)
        """
        PROXY_URLS = {
            'http': 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt',
            'socks4': 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt',
            'socks5': 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt',
        }

        print("Fetching proxies from TheSpeedX/PROXY-List...")
        all_proxies = []

        for proxy_type in self.proxy_types:
            if proxy_type not in PROXY_URLS:
                print(f"Unknown proxy type: {proxy_type}")
                continue

            try:
                print(f"  Fetching {proxy_type} proxies...")
                response = requests.get(PROXY_URLS[proxy_type], timeout=10)
                response.raise_for_status()

                lines = response.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxy_url = f"{proxy_type}://{line}"
                        all_proxies.append({
                            'http': proxy_url,
                            'https': proxy_url,
                            'type': proxy_type,
                            'address': line
                        })

                print(f"    Loaded {len(lines)} {proxy_type} proxies")
            except Exception as e:
                print(f"    Failed to fetch {proxy_type} proxies: {e}")

        self.proxies = all_proxies
        print(f"\nTotal proxies loaded: {len(self.proxies)}")
        return len(self.proxies)

    def fetch_proxies_fresh_list(self) -> int:
        """
        Fetch proxies from Fresh Proxy List (vakhov/fresh-proxy-list)
        Updates every 5-20 minutes, ~89% success rate
        Source: https://vakhov.github.io/fresh-proxy-list/proxylist.txt
        """
        print("Fetching proxies from Fresh Proxy List...")
        all_proxies = []

        try:
            response = requests.get(self.FRESH_PROXY_URL, timeout=10)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Format: IP:PORT or PROTOCOL://IP:PORT
                    if '://' in line:
                        # Already has protocol
                        parts = line.split('://')
                        protocol = parts[0]
                        address = parts[1]
                    else:
                        # No protocol, assume http
                        protocol = 'http'
                        address = line
                    
                    proxy_url = f"{protocol}://{address}"
                    all_proxies.append({
                        'http': proxy_url,
                        'https': proxy_url,
                        'type': protocol,
                        'address': address
                    })

            print(f"  Loaded {len(all_proxies)} proxies from Fresh List")
            print(f"  Expected success rate: ~89%")
            
        except Exception as e:
            print(f"  Failed to fetch fresh proxy list: {e}")

        self.proxies = all_proxies
        print(f"\nTotal proxies loaded: {len(self.proxies)}")
        return len(self.proxies)

    def fetch_proxies(self, limit: int = 500) -> int:
        """
        Fetch proxies from configured source

        Args:
            limit: Number of proxies to fetch (for GeoNode API)
        """
        if self.use_fresh_list:
            return self.fetch_proxies_fresh_list()
        elif self.use_geonode:
            return self.fetch_proxies_geonode(limit=limit, min_uptime=50.0)
        else:
            # Legacy TheSpeedX method (not recommended)
            return self.fetch_proxies_speedx()

    def test_proxy(self, proxy: Dict[str, str], timeout: int = 10) -> bool:
        """Test if a proxy is working"""
        try:
            response = requests.get(
                self.test_url,
                proxies=proxy,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except:
            return False

    def validate_proxies(self, max_test: int = 100, timeout: int = 10) -> int:
        """
        Validate a subset of proxies

        Args:
            max_test: Maximum number of proxies to test
            timeout: Timeout for each test in seconds
        """
        if not self.proxies:
            print("No proxies to validate. Call fetch_proxies() first.")
            return 0

        print(f"\nValidating proxies (testing up to {max_test} proxies)...")
        test_sample = random.sample(self.proxies, min(max_test, len(self.proxies)))

        working = []
        for i, proxy in enumerate(test_sample, 1):
            if i % 10 == 0:
                print(f"  Tested {i}/{len(test_sample)}... Found {len(working)} working")

            if self.test_proxy(proxy, timeout=timeout):
                working.append(proxy)

            # Don't test too many if we already have enough working proxies
            if len(working) >= 20:
                print(f"  Found {len(working)} working proxies, stopping validation")
                break

        self.working_proxies = working
        print(f"\nValidation complete: {len(working)} working proxies out of {len(test_sample)} tested")
        return len(working)

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get next proxy in rotation
        Falls back to all proxies if no working proxies are available
        """
        with self.lock:
            # Use working proxies if available, otherwise use all proxies
            pool = self.working_proxies if self.working_proxies else self.proxies

            if not pool:
                return None

            # Round-robin rotation
            proxy = pool[self.current_index % len(pool)]
            self.current_index += 1

            # Skip recently failed proxies
            attempts = 0
            while proxy['address'] in self.failed_proxies and attempts < len(pool):
                proxy = pool[self.current_index % len(pool)]
                self.current_index += 1
                attempts += 1

            return proxy

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the pool"""
        pool = self.working_proxies if self.working_proxies else self.proxies

        if not pool:
            return None

        # Filter out recently failed proxies
        available = [p for p in pool if p['address'] not in self.failed_proxies]

        if not available:
            # If all proxies failed, clear the failed set and try again
            self.failed_proxies.clear()
            available = pool

        return random.choice(available)

    def mark_proxy_failed(self, proxy: Dict[str, str]):
        """Mark a proxy as failed"""
        if proxy:
            with self.lock:
                self.failed_proxies.add(proxy['address'])
                self.proxy_stats[proxy['address']]['failed'] += 1

                # Remove from failed set after too many failures
                if len(self.failed_proxies) > len(self.proxies) * 0.8:
                    # Clear old failures to give proxies another chance
                    self.failed_proxies.clear()

    def mark_proxy_success(self, proxy: Dict[str, str]):
        """Mark a proxy as successful"""
        if proxy:
            with self.lock:
                # Remove from failed set if it succeeded
                self.failed_proxies.discard(proxy['address'])
                self.proxy_stats[proxy['address']]['success'] += 1

    def get_stats(self) -> Dict:
        """Get proxy usage statistics"""
        return {
            'total_proxies': len(self.proxies),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'current_index': self.current_index,
        }

    def print_stats(self):
        """Print proxy statistics"""
        stats = self.get_stats()
        print(f"\nProxy Statistics:")
        print(f"  Total proxies: {stats['total_proxies']}")
        print(f"  Working proxies: {stats['working_proxies']}")
        print(f"  Currently failed: {stats['failed_proxies']}")
        print(f"  Requests made: {stats['current_index']}")
