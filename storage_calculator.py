#!/usr/bin/env python3
"""
Calculate storage requirements for scraping 1.5M products
"""

# Based on actual test data
URLS_PER_FILE = 10_000
URL_FILE_SIZE_MB = 0.647  # 647KB for 10K URLs

PRODUCTS_PER_FILE = 299  # From your test run
SCRAPED_JSON_SIZE_MB = 0.291  # 291KB for 299 products

# Target
TOTAL_PRODUCTS = 1_500_000

# Calculations
print("="*70)
print("STORAGE CALCULATION FOR 1.5M PRODUCTS")
print("="*70)
print()

# 1. URL file storage
url_file_size = (TOTAL_PRODUCTS / URLS_PER_FILE) * URL_FILE_SIZE_MB
print(f"1. URL Files Storage:")
print(f"   - URL file (TXT):     {url_file_size:.1f} MB")
print(f"   - URL file (JSON):    {url_file_size * 1.5:.1f} MB (JSON is ~1.5x larger)")
print(f"   - Total URL files:    {url_file_size * 2.5:.1f} MB (~{url_file_size * 2.5 / 1024:.2f} GB)")
print()

# 2. Scraped data storage
avg_size_per_product_kb = (SCRAPED_JSON_SIZE_MB * 1024) / PRODUCTS_PER_FILE
avg_size_per_product_mb = avg_size_per_product_kb / 1024

print(f"2. Scraped Product Data:")
print(f"   - Average per product: {avg_size_per_product_kb:.2f} KB")
print(f"   - JSON for 1.5M:      {TOTAL_PRODUCTS * avg_size_per_product_mb:.1f} MB (~{TOTAL_PRODUCTS * avg_size_per_product_mb / 1024:.2f} GB)")
print(f"   - CSV for 1.5M:       {TOTAL_PRODUCTS * avg_size_per_product_mb * 0.8:.1f} MB (~{TOTAL_PRODUCTS * avg_size_per_product_mb * 0.8 / 1024:.2f} GB)")
print(f"                         (CSV is typically 20% smaller)")
print()

# 3. Progress saves (every 1000 products)
progress_saves = TOTAL_PRODUCTS // 1000
progress_size = progress_saves * (1000 * avg_size_per_product_mb)

print(f"3. Progress Saves (every 1000 products):")
print(f"   - Number of saves:    {progress_saves:,}")
print(f"   - Total size:         {progress_size:.1f} MB (~{progress_size / 1024:.2f} GB)")
print()

# 4. Total storage needed
json_total = TOTAL_PRODUCTS * avg_size_per_product_mb
csv_total = json_total * 0.8
url_total = url_file_size * 2.5
progress_total = progress_size

# With progress files
total_with_progress = json_total + csv_total + url_total + progress_total
total_with_progress_gb = total_with_progress / 1024

# Final files only (after cleanup)
total_final = json_total + csv_total + url_total
total_final_gb = total_final / 1024

print(f"4. TOTAL STORAGE REQUIREMENTS:")
print(f"   During scraping (with progress saves):")
print(f"   - Total:              {total_with_progress:.1f} MB ({total_with_progress_gb:.2f} GB)")
print()
print(f"   After cleanup (final files only):")
print(f"   - Total:              {total_final:.1f} MB ({total_final_gb:.2f} GB)")
print()

# Recommendations
print("="*70)
print("STORAGE RECOMMENDATIONS")
print("="*70)
print()

if total_with_progress_gb < 5:
    print("✅ MINIMAL: 5-10 GB free space is sufficient")
elif total_with_progress_gb < 20:
    print("✅ COMFORTABLE: 20-30 GB free space recommended")
else:
    print("⚠️  LARGE: 50+ GB free space recommended")

print()
print("Breakdown by storage type:")
print(f"  - Minimum (final files only):     {total_final_gb:.1f} GB")
print(f"  - Recommended (with progress):    {total_with_progress_gb:.1f} GB")
print(f"  - Safe (with 50% buffer):         {total_with_progress_gb * 1.5:.1f} GB")
print()

print("="*70)
print("ADDITIONAL CONSIDERATIONS")
print("="*70)
print()
print("1. Database storage (if importing to DB):")
print(f"   - PostgreSQL/MySQL:   {total_final_gb * 2:.1f} GB (with indexes)")
print(f"   - MongoDB:            {total_final_gb * 1.5:.1f} GB (BSON format)")
print()
print("2. Compressed archives:")
print(f"   - ZIP/GZIP (JSON):    {total_final_gb * 0.2:.1f} GB (~80% compression)")
print(f"   - ZIP/GZIP (CSV):     {total_final_gb * 0.15:.1f} GB (~85% compression)")
print()
print("3. Working space during processing:")
print(f"   - Temporary files:    1-2 GB")
print(f"   - Failed URLs logs:   <100 MB")
print(f"   - System overhead:    1-2 GB")
print()

print("="*70)
print("RECOMMENDED SERVER SPECS")
print("="*70)
print()
print("For 1.5M products scraping:")
print(f"  💾 Storage:  {int(total_with_progress_gb * 2)} GB minimum ({int(total_with_progress_gb * 3)} GB recommended)")
print(f"  💻 RAM:      16 GB (for 20 workers)")
print(f"  🔧 CPU:      4+ cores")
print(f"  🌐 Network:  100+ Mbps")
print()

# Time estimates
products_per_second = 2.0  # Conservative estimate with 10 workers
total_seconds = TOTAL_PRODUCTS / products_per_second
total_hours = total_seconds / 3600
total_days = total_hours / 24

print("⏱️  TIME ESTIMATES:")
print(f"  With 10 workers:  {total_hours:.1f} hours (~{total_days:.1f} days)")
print(f"  With 20 workers:  {total_hours/2:.1f} hours (~{total_days/2:.1f} days)")
print(f"  With 30 workers:  {total_hours/3:.1f} hours (~{total_days/3:.1f} days)")
print()

print("="*70)
