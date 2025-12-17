#!/bin/bash

# Deploy Production Scraper with Webshare to Server
# Usage: ./deploy_production_webshare.sh

SERVER_IP="72.61.18.34"
SERVER_USER="root"
WEBSHARE_API_KEY="hqy10ekhqb0jackvwe9fyzf4aosmo28wi6s48zji"

echo "=========================================="
echo "DEPLOYING PRODUCTION SCRAPER WITH WEBSHARE"
echo "=========================================="
echo ""
echo "Target server: $SERVER_USER@$SERVER_IP"
echo ""

# Upload the script
echo "Step 1: Uploading production scraper..."
scp production_scraper_webshare.py $SERVER_USER@$SERVER_IP:~/mrosupply_scraper/

echo ""
echo "Step 2: Installing dependencies on server..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd ~/mrosupply_scraper
echo "Installing required packages..."
pip3 install beautifulsoup4 requests lxml --break-system-packages 2>/dev/null || pip3 install beautifulsoup4 requests lxml
chmod +x production_scraper_webshare.py
echo "✅ Setup complete!"
ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "To run the scraper:"
echo ""
echo "  1. SSH into server:"
echo "     ssh $SERVER_USER@$SERVER_IP"
echo ""
echo "  2. Start scraper in screen:"
echo "     cd ~/mrosupply_scraper"
echo "     screen -S scraper"
echo "     python3 production_scraper_webshare.py --webshare-api-key $WEBSHARE_API_KEY --workers 20 --delay 0.3"
echo ""
echo "  3. Detach from screen:"
echo "     Press: Ctrl+A, then D"
echo ""
echo "  4. Reattach later:"
echo "     screen -r scraper"
echo ""
echo "=========================================="
echo "Quick start command (run on server):"
echo "screen -dmS scraper bash -c 'cd ~/mrosupply_scraper && python3 production_scraper_webshare.py --webshare-api-key $WEBSHARE_API_KEY --workers 20 --delay 0.3'"
echo "=========================================="
