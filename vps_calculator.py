#!/usr/bin/env python3
"""
VPS Performance Calculator for Large-Scale Scraping
Calculates optimal settings and time estimates for your specific hardware
"""

def calculate_estimates(total_products, ram_gb, cores):
    """Calculate scraping estimates based on hardware"""

    print(f"{'='*70}")
    print(f"VPS SCRAPING CALCULATOR")
    print(f"{'='*70}")
    print(f"Hardware: {ram_gb}GB RAM, {cores} CPU cores")
    print(f"Target: {total_products:,} products")
    print(f"{'='*70}\n")

    # Performance scenarios based on hardware
    scenarios = []

    # Conservative: 2-3 workers per core
    workers_conservative = cores * 2
    rate_conservative = workers_conservative * 0.8  # 0.8 products/s per worker
    scenarios.append(("Conservative (Safe)", workers_conservative, rate_conservative))

    # Balanced: 4-5 workers per core
    workers_balanced = cores * 4
    rate_balanced = workers_balanced * 0.7  # 0.7 products/s per worker
    scenarios.append(("Balanced (Recommended)", workers_balanced, rate_balanced))

    # Aggressive: 6-8 workers per core
    workers_aggressive = cores * 7
    rate_aggressive = workers_aggressive * 0.6  # 0.6 products/s per worker
    scenarios.append(("Aggressive (Fast)", workers_aggressive, rate_aggressive))

    # Very Aggressive: 10+ workers per core (if RAM allows)
    if ram_gb >= 8:
        workers_very_aggressive = cores * 10
        rate_very_aggressive = workers_very_aggressive * 0.5  # 0.5 products/s per worker
        scenarios.append(("Very Aggressive (Max Speed)", workers_very_aggressive, rate_very_aggressive))

    print(f"PERFORMANCE ESTIMATES:\n")
    print(f"{'Scenario':<30} {'Workers':<10} {'Speed':<15} {'Time':<20}")
    print(f"{'-'*75}")

    for scenario_name, workers, rate in scenarios:
        time_seconds = total_products / rate
        time_minutes = time_seconds / 60
        time_hours = time_minutes / 60

        if time_hours < 1:
            time_str = f"{time_minutes:.1f} minutes"
        elif time_hours < 24:
            time_str = f"{time_hours:.1f} hours"
        else:
            days = time_hours / 24
            time_str = f"{days:.1f} days ({time_hours:.1f}h)"

        print(f"{scenario_name:<30} {workers:<10} {rate:.1f}/s{'':<9} {time_str:<20}")

    print(f"\n{'='*70}\n")

    # Recommended configuration
    recommended_workers = cores * 4
    recommended_rate = recommended_workers * 0.7
    recommended_time_hours = total_products / recommended_rate / 3600

    print(f"RECOMMENDED CONFIGURATION:")
    print(f"  Workers: {recommended_workers}")
    print(f"  Expected Speed: {recommended_rate:.1f} products/second")
    print(f"  Estimated Time: {recommended_time_hours:.1f} hours")

    if recommended_time_hours > 2:
        print(f"  Note: This exceeds 2 hours target")
        # Calculate what's needed for 2 hours
        needed_rate = total_products / (2 * 3600)
        needed_workers = int(needed_rate / 0.6) + 1
        print(f"\n  To finish in 2 hours, you would need:")
        print(f"    - {needed_workers} workers")
        print(f"    - {needed_rate:.1f} products/second")
        print(f"    - This may cause rate limiting!")

    print(f"\n{'='*70}\n")

    # Memory estimate
    mem_per_worker = 50  # MB per worker (rough estimate)
    total_mem_mb = recommended_workers * mem_per_worker
    total_mem_gb = total_mem_mb / 1024

    print(f"MEMORY USAGE ESTIMATE:")
    print(f"  Per worker: ~{mem_per_worker}MB")
    print(f"  Total ({recommended_workers} workers): ~{total_mem_gb:.1f}GB")
    print(f"  Available RAM: {ram_gb}GB")

    if total_mem_gb < ram_gb * 0.7:
        print(f"  Status: ✅ Plenty of RAM available")
    elif total_mem_gb < ram_gb:
        print(f"  Status: ⚠️  RAM usage is high but acceptable")
    else:
        print(f"  Status: ❌ Insufficient RAM - reduce workers!")

    print(f"\n{'='*70}\n")

    # Batch processing recommendation
    if recommended_time_hours > 12:
        batch_size = int(total_products / (recommended_time_hours / 6))  # 6-hour batches
        num_batches = (total_products + batch_size - 1) // batch_size

        print(f"BATCH PROCESSING STRATEGY (Recommended for long runs):")
        print(f"  Break into {num_batches} batches of ~{batch_size:,} products each")
        print(f"  Each batch: ~6 hours")
        print(f"  Benefits: Resume capability, progress checkpoints, safer")
        print(f"\n{'='*70}\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) >= 4:
        total_products = int(sys.argv[1])
        ram_gb = int(sys.argv[2])
        cores = int(sys.argv[3])
    else:
        print("VPS Scraping Calculator")
        print("Usage: python3 vps_calculator.py <total_products> <ram_gb> <cores>")
        print("\nUsing default values for demonstration...\n")
        total_products = 1508692
        ram_gb = 16
        cores = 4

    calculate_estimates(total_products, ram_gb, cores)

    print("\nRECOMMENDED COMMANDS:\n")
    recommended_workers = cores * 4

    print(f"# Test first (100 products):")
    print(f"python3 fast_scraper.py --max-products 100 --workers {recommended_workers}\n")

    print(f"# Full scrape (recommended):")
    print(f"python3 fast_scraper.py --workers {recommended_workers}\n")

    print(f"# Aggressive (faster but riskier):")
    aggressive_workers = cores * 7
    print(f"python3 fast_scraper.py --workers {aggressive_workers}\n")
