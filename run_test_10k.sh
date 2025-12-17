#!/bin/bash

# Quick Test Script - 10K products with 10 proxies
# Usage: ./run_test_10k.sh

WEBSHARE_API_KEY="hqy10ekhqb0jackvwe9fyzf4aosmo28wi6s48zji"

echo "=========================================="
echo "TEST: 10,000 PRODUCTS WITH 10 PROXIES"
echo "=========================================="
echo ""

python3 test_10k_webshare.py \
  --webshare-api-key $WEBSHARE_API_KEY \
  --workers 10 \
  --delay 0.5 \
  --target 10000 \
  --output-dir test_10k_data

echo ""
echo "=========================================="
echo "Test complete! Check test_10k_data/ for results"
echo "=========================================="
