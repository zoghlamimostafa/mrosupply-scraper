#!/usr/bin/env python3
"""
Enhanced headers and browser fingerprinting to avoid detection
"""

import random
from typing import Dict

class BrowserFingerprint:
    """Generate realistic browser fingerprints"""

    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',

        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    ]

    @staticmethod
    def get_realistic_headers(referer: str = None) -> Dict[str, str]:
        """Generate realistic browser headers"""
        user_agent = random.choice(BrowserFingerprint.USER_AGENTS)

        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin' if referer else 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }

        # Add Chrome-specific headers if Chrome user agent
        if 'Chrome' in user_agent and 'Edg' not in user_agent:
            headers['sec-ch-ua'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
            headers['sec-ch-ua-mobile'] = '?0'
            headers['sec-ch-ua-platform'] = '"Windows"' if 'Windows' in user_agent else '"macOS"'

        # Add referer if provided
        if referer:
            headers['Referer'] = referer

        return headers

    @staticmethod
    def get_search_referer(base_url: str) -> str:
        """Get a realistic referer for search pages"""
        return f"{base_url}/"

    @staticmethod
    def get_product_referer(base_url: str) -> str:
        """Get a realistic referer for product pages"""
        return f"{base_url}/search/"


def test_headers():
    """Test header generation"""
    print("Testing browser fingerprint generation...\n")

    for i in range(3):
        print(f"Sample {i+1}:")
        headers = BrowserFingerprint.get_realistic_headers(
            referer="https://www.mrosupply.com/search/"
        )
        print(f"  User-Agent: {headers['User-Agent'][:80]}...")
        print(f"  Accept: {headers['Accept'][:60]}...")
        print(f"  Sec-Fetch-Site: {headers.get('Sec-Fetch-Site', 'N/A')}")
        print(f"  Referer: {headers.get('Referer', 'N/A')}")
        if 'sec-ch-ua' in headers:
            print(f"  sec-ch-ua: {headers['sec-ch-ua']}")
        print()


if __name__ == '__main__':
    test_headers()
