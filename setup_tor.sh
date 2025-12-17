#!/bin/bash

# Setup Tor for Scraping
# Usage: ./setup_tor.sh [number_of_instances]

NUM_INSTANCES=${1:-1}  # Default: 1 instance

echo "=========================================="
echo "TOR SETUP FOR SCRAPING"
echo "=========================================="
echo ""
echo "Setting up $NUM_INSTANCES Tor instance(s)..."
echo ""

# Check if Tor is installed
if ! command -v tor &> /dev/null; then
    echo "Installing Tor..."
    sudo apt update
    sudo apt install tor -y
else
    echo "✅ Tor is already installed"
fi

echo ""
echo "Configuring Tor instance(s)..."

if [ $NUM_INSTANCES -eq 1 ]; then
    # Single instance - simple config
    echo "Setting up single Tor instance on port 9050..."

    sudo tee /etc/tor/torrc > /dev/null <<EOF
# Tor Configuration for Scraping
SOCKSPort 9050
ControlPort 9051
CookieAuthentication 0
DataDirectory /var/lib/tor
EOF

    echo "✅ Configuration written to /etc/tor/torrc"

else
    # Multiple instances
    echo "Setting up $NUM_INSTANCES Tor instances..."

    for i in $(seq 1 $NUM_INSTANCES); do
        SOCKS_PORT=$((9050 + i - 1))
        CONTROL_PORT=$((9051 + i - 1))
        DATA_DIR="/var/lib/tor/instance$i"

        echo "  Instance $i: SOCKS=$SOCKS_PORT, Control=$CONTROL_PORT"

        # Create data directory
        sudo mkdir -p $DATA_DIR
        sudo chown -R debian-tor:debian-tor $DATA_DIR

        # Create config file
        sudo tee /etc/tor/torrc.instance$i > /dev/null <<EOF
SOCKSPort $SOCKS_PORT
ControlPort $CONTROL_PORT
DataDirectory $DATA_DIR
CookieAuthentication 0
EOF
    done

    echo "✅ Configured $NUM_INSTANCES instances"
fi

echo ""
echo "Starting Tor..."

# Stop existing Tor service
sudo systemctl stop tor 2>/dev/null

if [ $NUM_INSTANCES -eq 1 ]; then
    # Start single instance
    sudo systemctl start tor
    sudo systemctl enable tor
    sleep 3
else
    # Start multiple instances
    for i in $(seq 1 $NUM_INSTANCES); do
        tor -f /etc/tor/torrc.instance$i &
        sleep 1
    done
    sleep 3
fi

echo ""
echo "Testing Tor connection(s)..."
echo ""

# Test connections
if [ $NUM_INSTANCES -eq 1 ]; then
    RESULT=$(curl --socks5 127.0.0.1:9050 -s https://check.torproject.org/api/ip 2>/dev/null)
    if echo "$RESULT" | grep -q '"IsTor":true'; then
        IP=$(echo "$RESULT" | grep -o '"IP":"[^"]*' | cut -d'"' -f4)
        echo "✅ Tor port 9050: Working (IP: $IP)"
    else
        echo "❌ Tor port 9050: Not working"
    fi
else
    for i in $(seq 1 $NUM_INSTANCES); do
        PORT=$((9050 + i - 1))
        RESULT=$(curl --socks5 127.0.0.1:$PORT -s https://check.torproject.org/api/ip 2>/dev/null)
        if echo "$RESULT" | grep -q '"IsTor":true'; then
            IP=$(echo "$RESULT" | grep -o '"IP":"[^"]*' | cut -d'"' -f4)
            echo "✅ Tor port $PORT: Working (IP: $IP)"
        else
            echo "❌ Tor port $PORT: Not working"
        fi
    done
fi

echo ""
echo "=========================================="
echo "TOR SETUP COMPLETE!"
echo "=========================================="
echo ""

if [ $NUM_INSTANCES -eq 1 ]; then
    echo "Tor is running on:"
    echo "  SOCKS port: 9050"
    echo "  Control port: 9051"
    echo ""
    echo "Test with:"
    echo "  curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip"
    echo ""
    echo "Run scraper with:"
    echo "  python3 tor_scraper.py --tor-ports 9050 --max-products 100"
else
    echo "Tor instances running on ports:"
    for i in $(seq 1 $NUM_INSTANCES); do
        echo "  Instance $i: 9050$((i-1))"
    done
    echo ""
    PORTS=$(seq -s, 9050 $((9050 + NUM_INSTANCES - 1)))
    echo "Run scraper with:"
    echo "  python3 tor_scraper.py --tor-ports $PORTS --workers $NUM_INSTANCES --max-products 100"
fi

echo ""
echo "=========================================="
