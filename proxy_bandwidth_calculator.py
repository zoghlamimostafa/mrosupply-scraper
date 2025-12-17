#!/usr/bin/env python3
"""
Calculate Webshare Proxy Bandwidth Requirements for 1.5M Products
"""

# Webshare Rotating Residential Pricing
PRICING = {
    '1GB': {'bandwidth_gb': 1, 'price_per_gb': 3.50, 'total': 3.50},
    '100GB': {'bandwidth_gb': 100, 'price_per_gb': 2.25, 'total': 225.00},
    '3000GB': {'bandwidth_gb': 3000, 'price_per_gb': 1.40, 'total': 4200.00},
}

# Product scraping estimates
TOTAL_PRODUCTS = 1_500_000

# Average HTML page size for product pages (based on typical e-commerce sites)
AVG_PAGE_SIZE_KB = 250  # Conservative estimate (includes HTML, images in page, CSS, JS)
AVG_PAGE_SIZE_MB = AVG_PAGE_SIZE_KB / 1024

# Calculate bandwidth needed
print("="*70)
print("WEBSHARE PROXY BANDWIDTH CALCULATOR")
print("="*70)
print()

print(f"Target: {TOTAL_PRODUCTS:,} products")
print(f"Average page size: {AVG_PAGE_SIZE_KB} KB ({AVG_PAGE_SIZE_MB:.2f} MB)")
print()

# Total bandwidth calculation
total_bandwidth_mb = TOTAL_PRODUCTS * AVG_PAGE_SIZE_MB
total_bandwidth_gb = total_bandwidth_mb / 1024

print("="*70)
print("BANDWIDTH REQUIREMENTS")
print("="*70)
print()
print(f"Total bandwidth needed: {total_bandwidth_mb:,.0f} MB ({total_bandwidth_gb:.2f} GB)")
print()

# Factor in overhead (retries, failed requests, redirects)
overhead_factor = 1.15  # 15% overhead for retries
total_with_overhead_gb = total_bandwidth_gb * overhead_factor

print(f"With 15% overhead (retries/failures): {total_with_overhead_gb:.2f} GB")
print()

# Cost analysis for each plan
print("="*70)
print("COST ANALYSIS - WEBSHARE ROTATING RESIDENTIAL PROXIES")
print("="*70)
print()

for plan_name, plan_data in PRICING.items():
    bandwidth_gb = plan_data['bandwidth_gb']
    price_per_gb = plan_data['price_per_gb']
    total_price = plan_data['total']

    # How many full scrapes can we do?
    full_scrapes = bandwidth_gb / total_with_overhead_gb

    # Cost per scrape
    cost_per_scrape = total_price / full_scrapes if full_scrapes >= 1 else total_price

    # Cost for 1.5M products
    if bandwidth_gb >= total_with_overhead_gb:
        enough = "✅ ENOUGH"
        products_possible = TOTAL_PRODUCTS
    else:
        enough = "❌ NOT ENOUGH"
        products_possible = int((bandwidth_gb / total_with_overhead_gb) * TOTAL_PRODUCTS)

    print(f"{plan_name} Plan:")
    print(f"  Bandwidth:        {bandwidth_gb} GB")
    print(f"  Price per GB:     ${price_per_gb:.2f}")
    print(f"  Total price:      ${total_price:.2f}/month")
    print(f"  Full scrapes:     {full_scrapes:.2f}x")
    print(f"  Products:         {products_possible:,} {enough}")
    if bandwidth_gb >= total_with_overhead_gb:
        print(f"  Cost per scrape:  ${cost_per_scrape:.2f}")
        leftover = bandwidth_gb - total_with_overhead_gb
        print(f"  Leftover:         {leftover:.2f} GB")
    print()

print("="*70)
print("RECOMMENDATIONS")
print("="*70)
print()

# Determine best plan
if total_with_overhead_gb <= 1:
    recommended = "1GB"
    print(f"✅ RECOMMENDED: 1GB Plan (${PRICING['1GB']['total']:.2f}/month)")
    print(f"   Perfect for 1.5M products")
elif total_with_overhead_gb <= 100:
    recommended = "100GB"
    print(f"✅ RECOMMENDED: 100GB Plan (${PRICING['100GB']['total']:.2f}/month)")
    print(f"   Good for multiple scrapes")
else:
    recommended = "3000GB"
    print(f"✅ RECOMMENDED: 3000GB Plan (${PRICING['3000GB']['total']:.2f}/month)")
    print(f"   For large-scale scraping")

print()

# Alternative: Without proxies (direct scraping)
print("="*70)
print("ALTERNATIVE: SCRAPING WITHOUT PROXIES")
print("="*70)
print()
print("Pros:")
print("  ✅ FREE - No proxy costs")
print("  ✅ Faster - No proxy latency")
print("  ✅ Simpler - Less complexity")
print()
print("Cons:")
print("  ⚠️  Risk of IP blocking")
print("  ⚠️  Need slower scraping (higher delay)")
print("  ⚠️  May get rate limited")
print()
print("Recommendation for 1.5M products:")
print("  - Use 2-5 workers (instead of 10-20)")
print("  - Use 2-3 second delay (instead of 0.5s)")
print("  - Expected time: 15-20 days (instead of 8-10 days)")
print("  - Cost: $0 (vs proxy costs)")
print()

# ROI calculation
print("="*70)
print("COST vs TIME TRADE-OFF")
print("="*70)
print()

scenarios = [
    {
        'name': 'Without Proxies (Slow & Safe)',
        'workers': 5,
        'delay': 2.0,
        'proxy_cost': 0,
    },
    {
        'name': 'With 1GB Proxies (Fast)',
        'workers': 10,
        'delay': 0.5,
        'proxy_cost': 3.50,
    },
    {
        'name': 'With 100GB Proxies (Very Fast)',
        'workers': 20,
        'delay': 0.3,
        'proxy_cost': 225.00,
    },
]

for scenario in scenarios:
    workers = scenario['workers']
    delay = scenario['delay']
    proxy_cost = scenario['proxy_cost']

    # Calculate time
    products_per_second = workers / delay
    total_seconds = TOTAL_PRODUCTS / products_per_second
    total_hours = total_seconds / 3600
    total_days = total_hours / 24

    print(f"{scenario['name']}:")
    print(f"  Workers: {workers}, Delay: {delay}s")
    print(f"  Speed: ~{products_per_second:.1f} products/second")
    print(f"  Time: {total_hours:.1f} hours ({total_days:.1f} days)")
    print(f"  Proxy cost: ${proxy_cost:.2f}/month")
    print(f"  Cost per day: ${proxy_cost/30:.2f}")
    print()

print("="*70)
print("FINAL RECOMMENDATION")
print("="*70)
print()

if total_with_overhead_gb <= 100:
    print(f"💡 For 1.5M products ({total_with_overhead_gb:.1f} GB needed):")
    print()
    print("OPTION 1: Without Proxies (FREE)")
    print("  Cost: $0")
    print("  Time: ~15-20 days")
    print("  Risk: Possible IP blocking")
    print()
    print("OPTION 2: With 100GB Proxies ($225/month)")
    print("  Cost: $225/month")
    print("  Time: ~4-5 days")
    print("  Risk: Very low")
    print("  You can scrape 1.5M products multiple times")
    print()
    print("💰 BEST VALUE: Start without proxies (FREE)")
    print("   - If you get blocked, then buy 1GB plan ($3.50)")
    print("   - This way you only pay if needed")
else:
    print(f"⚠️  High bandwidth needed: {total_with_overhead_gb:.1f} GB")
    print(f"   Consider buying 100GB plan for ${PRICING['100GB']['total']:.2f}/month")

print()
print("="*70)
