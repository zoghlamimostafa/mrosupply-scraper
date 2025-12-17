# How to Upload and Run Scraper on Your VPS

## Method 1: Using SCP (From Your Computer)

### Step 1: Open Terminal on Your Computer

```bash
# Navigate to the scraper directory
cd /home/user/Desktop

# Upload all files to VPS
scp -r mrosupply.com info@srv1164617.hstgr.cloud:/home/info/

# Enter password when prompted: F7FZndcl#XyunvuiG@9s
```

### Step 2: SSH into VPS and Run Setup

```bash
# Connect to VPS
ssh info@srv1164617.hstgr.cloud

# Navigate to directory
cd mrosupply.com

# Make scripts executable
chmod +x *.sh

# Run setup script
./vps_setup.sh

# Start scraping
./start_scraping.sh

# Disconnect (scraper keeps running)
# Press Ctrl+D or type: exit
```

---

## Method 2: Using FileZilla (GUI)

### Step 1: Download FileZilla
- Download from: https://filezilla-project.org/

### Step 2: Connect to VPS
```
Host: sftp://srv1164617.hstgr.cloud
Username: info
Password: F7FZndcl#XyunvuiG@9s
Port: 22
```

### Step 3: Upload Files
- Left side: Navigate to `/home/user/Desktop/mrosupply.com`
- Right side: Navigate to `/home/info/`
- Drag all files from left to right

### Step 4: Run Setup via SSH
```bash
ssh info@srv1164617.hstgr.cloud
cd mrosupply.com
chmod +x *.sh
./vps_setup.sh
./start_scraping.sh
```

---

## Method 3: Manual Commands (Copy-Paste)

Connect to your VPS and run these commands one by one:

```bash
# Update system
sudo apt update -y && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip screen

# Install Python packages
pip3 install beautifulsoup4 requests lxml

# Create directory
mkdir -p ~/scraper
cd ~/scraper

# Now upload files using FileZilla or WinSCP

# After upload, make scripts executable
chmod +x *.sh

# Test the scraper
python3 vps_calculator.py 1508692 16 4

# Start scraping in screen
screen -S scraper
python3 batch_scraper.py --workers 16 --batch-size 241920

# Detach: Ctrl+A, then D
```

---

## Monitoring Commands

```bash
# Check if scraper is running
screen -list

# View live progress
screen -r scraper

# Check files
ls -lh scraped_data/

# Check batch state
cat scraped_data/batch_state.json | python3 -m json.tool

# Check disk space
df -h

# Check memory
free -h

# Check how many products scraped
find scraped_data -name "batch_*.json" -exec grep -c '"url"' {} \; | awk '{s+=$1} END {print s}'
```

---

## Quick Commands Summary

```bash
# Upload from local computer
scp -r mrosupply.com info@srv1164617.hstgr.cloud:/home/info/

# Connect to VPS
ssh info@srv1164617.hstgr.cloud

# Setup
cd mrosupply.com
chmod +x *.sh
./vps_setup.sh

# Start scraping
./start_scraping.sh

# Monitor
screen -r scraper

# Detach
Ctrl+A, then D
```

---

## After Completion

Download results to your local computer:

```bash
# On your local computer
scp -r info@srv1164617.hstgr.cloud:/home/info/mrosupply.com/scraped_data ./

# This will download:
# - products_final_all_batches.json (~4-6GB)
# - products_final_all_batches.csv (~2-3GB)
# - All batch files
```

---

## Troubleshooting

### Can't connect via SSH
```bash
# Try with port specified
ssh -p 22 info@srv1164617.hstgr.cloud

# Or try with verbose mode
ssh -v info@srv1164617.hstgr.cloud
```

### Permission denied for scripts
```bash
chmod +x vps_setup.sh start_scraping.sh quick_start.sh
```

### Python package not found
```bash
pip3 install --user beautifulsoup4 requests lxml
export PATH=$PATH:~/.local/bin
```

### Screen not found
```bash
sudo apt install screen -y
```

---

## Security Reminder

**IMPORTANT: Change your password after setup!**

```bash
# On VPS, run:
passwd

# Follow prompts to set new password
```

Even better, set up SSH keys:

```bash
# On your local computer
ssh-keygen -t rsa -b 4096
ssh-copy-id info@srv1164617.hstgr.cloud

# Then on VPS, disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```
