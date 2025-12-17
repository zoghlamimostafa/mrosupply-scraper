#!/bin/bash

# Deploy and run scraper on production server
# Usage: ./deploy_to_server.sh [server_ip] [user]

echo "=========================================="
echo "DEPLOYMENT SCRIPT FOR PRODUCTION SCRAPER"
echo "=========================================="
echo ""

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <server_ip> <user>"
    echo "Example: $0 192.168.1.100 root"
    echo ""
    exit 1
fi

SERVER_IP=$1
SERVER_USER=$2

echo "Target server: $SERVER_USER@$SERVER_IP"
echo ""

# Files to upload
FILES_TO_UPLOAD="production_scraper.py requirements.txt"

echo "Step 1: Testing SSH connection..."
if ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'Connection successful'"; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
    echo "Please check:"
    echo "  - Server IP is correct"
    echo "  - SSH is running on server"
    echo "  - You have SSH access"
    exit 1
fi

echo ""
echo "Step 2: Creating directory on server..."
ssh $SERVER_USER@$SERVER_IP "mkdir -p ~/mrosupply_scraper"

echo ""
echo "Step 3: Uploading files..."
for file in $FILES_TO_UPLOAD; do
    if [ -f "$file" ]; then
        echo "  Uploading $file..."
        scp "$file" $SERVER_USER@$SERVER_IP:~/mrosupply_scraper/
    else
        echo "  ⚠️  $file not found, skipping..."
    fi
done

echo ""
echo "Step 4: Installing dependencies on server..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd ~/mrosupply_scraper
echo "Updating system..."
sudo apt-get update -qq

echo "Installing Python and pip..."
sudo apt-get install -y python3 python3-pip

echo "Installing Python packages..."
pip3 install beautifulsoup4 requests lxml

echo "Installing screen for background execution..."
sudo apt-get install -y screen

echo "Making script executable..."
chmod +x production_scraper.py

echo ""
echo "✅ Setup complete!"
ENDSSH

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "To run the scraper on the server:"
echo ""
echo "  1. SSH into server:"
echo "     ssh $SERVER_USER@$SERVER_IP"
echo ""
echo "  2. Start screen session:"
echo "     screen -S scraper"
echo ""
echo "  3. Run the scraper:"
echo "     cd ~/mrosupply_scraper"
echo "     python3 production_scraper.py"
echo ""
echo "  4. Detach from screen (keep it running):"
echo "     Press: Ctrl+A, then D"
echo ""
echo "  5. Reattach later to check progress:"
echo "     screen -r scraper"
echo ""
echo "  6. Download results (from your local machine):"
echo "     scp -r $SERVER_USER@$SERVER_IP:~/mrosupply_scraper/production_data ./"
echo ""
echo "=========================================="
echo "Quick start command:"
echo "ssh $SERVER_USER@$SERVER_IP 'cd ~/mrosupply_scraper && screen -dmS scraper python3 production_scraper.py'"
echo "=========================================="
