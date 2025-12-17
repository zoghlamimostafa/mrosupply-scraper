# Complete Azure Deployment Guide
## Step-by-Step: Email + GitHub + Azure

---

## Overview

You'll be hosting the scraper on Azure Virtual Machine. Here's what you need:

1. ✉️ **Email (Gmail)** - For notifications
2. 🐙 **GitHub** - For code storage (optional)
3. ☁️ **Azure** - For hosting the scraper

**Total Setup Time:** 30-40 minutes
**Monthly Cost:** ~$50-100 (can delete after completion)

---

## Part 1: Email Setup (Gmail) ✉️

### Step 1: Create Gmail App Password

**Why:** Gmail requires app-specific passwords for SMTP access

**Steps:**

1. **Go to Google Account:**
   - Visit: https://myaccount.google.com
   - Login with your Gmail account

2. **Enable 2-Step Verification (if not enabled):**
   - Click "Security" in left menu
   - Find "2-Step Verification"
   - Click "Get Started"
   - Follow prompts to enable

3. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Or: Security → 2-Step Verification → App passwords (at bottom)
   - Select app: "Mail"
   - Select device: "Other (Custom name)"
   - Enter name: "MRO Scraper"
   - Click "Generate"

4. **Save the Password:**
   ```
   You'll get a 16-character password like: abcd efgh ijkl mnop
   IMPORTANT: Copy this now - you can't see it again!
   Save it as: your_app_password
   ```

### What You Need to Save:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=abcd efgh ijkl mnop  (the 16-char app password)
NOTIFICATION_EMAIL=your_email@gmail.com  (where to receive alerts)
```

---

## Part 2: GitHub Setup (Optional) 🐙

### Do You Need GitHub?

**You need GitHub if:**
- ✅ You want version control
- ✅ You want to use GitHub Actions (serverless option)
- ✅ You want to collaborate

**You DON'T need GitHub if:**
- ❌ Just deploying to Azure VM directly

### If You Want GitHub:

#### Step 1: Create GitHub Account
- Go to: https://github.com
- Click "Sign up"
- Follow prompts

#### Step 2: Create Repository

1. **Click "New repository"**
2. **Settings:**
   - Name: `mrosupply-scraper`
   - Description: "Autonomous web scraper for MRO Supply"
   - Public or Private: **Public** (for free Actions minutes)
   - Don't initialize with README
3. **Click "Create repository"**

#### Step 3: Push Your Code

```bash
# On your laptop
cd /home/user/Desktop/mrosupply.com

# Initialize git
git init
git add .
git commit -m "Initial commit - autonomous scraper"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/mrosupply-scraper.git

# Push
git branch -M main
git push -u origin main
```

#### Step 4: Add Secrets (for GitHub Actions)

If using GitHub Actions:

1. Go to your repo on GitHub
2. Click "Settings"
3. Click "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Add these secrets:

```
Name: PROXY_HOST
Value: p.webshare.io

Name: PROXY_PORT
Value: 10000

Name: PROXY_USER
Value: your_webshare_username

Name: PROXY_PASS
Value: your_webshare_password

Name: SMTP_HOST
Value: smtp.gmail.com

Name: SMTP_PORT
Value: 587

Name: SMTP_USER
Value: your_email@gmail.com

Name: SMTP_PASS
Value: your_16_char_app_password

Name: NOTIFICATION_EMAIL
Value: your_email@gmail.com
```

**Note:** If you're just using Azure VM, you can skip GitHub entirely.

---

## Part 3: Azure Setup ☁️

### Option A: Azure Virtual Machine (Recommended)

#### Step 1: Create Azure Account

1. **Go to:** https://azure.microsoft.com
2. **Click "Start free"** or "Sign in"
3. **New users get:**
   - $200 free credit for 30 days
   - 12 months of free services
   - Always free services

4. **Follow signup:**
   - Microsoft account (or create new)
   - Phone verification
   - Credit card (for verification - won't charge during free trial)

#### Step 2: Create Virtual Machine

**Method 1: Azure Portal (Easy)**

1. **Login to Azure Portal:**
   - Go to: https://portal.azure.com

2. **Create VM:**
   - Click "Create a resource"
   - Select "Virtual Machine"
   - Click "Create"

3. **Basics Tab:**
   ```
   Subscription: Your subscription
   Resource group: Create new → "mrosupply-scraper-rg"

   Virtual machine name: mrosupply-scraper-vm
   Region: East US (or closest to you)

   Availability options: No infrastructure redundancy required
   Security type: Standard

   Image: Ubuntu Server 22.04 LTS - x64 Gen2

   Size: Click "See all sizes"
         Search for: Standard_D8s_v3
         Specs: 8 vCPUs, 32 GB RAM
         Cost: ~$0.38/hour (~$274/month)
         Click "Select"

   Authentication type: SSH public key
   Username: azureuser
   SSH public key source: Generate new key pair
   Key pair name: mrosupply-vm-key
   ```

4. **Disks Tab:**
   ```
   OS disk type: Premium SSD (recommended)
   Delete with VM: Yes (check this)
   ```

5. **Networking Tab:**
   ```
   Virtual network: (default - new)
   Subnet: (default)
   Public IP: (default - new)

   NIC network security group: Basic
   Public inbound ports: Allow selected ports
   Select inbound ports: SSH (22), HTTP (80), HTTPS (443)

   ⚠️ IMPORTANT: We'll open port 8080 later for dashboard
   ```

6. **Management Tab:**
   ```
   Enable auto-shutdown: Yes (optional, saves money)
   Shutdown time: 2:00 AM (your timezone)
   ```

7. **Review + Create:**
   - Review settings
   - Estimated cost: ~$0.38/hour
   - Click "Create"
   - **DOWNLOAD the private key (.pem file)** - Save it securely!

8. **Wait for Deployment:**
   - Takes 2-3 minutes
   - Click "Go to resource" when done

#### Step 3: Connect to VM

**Get IP Address:**
- In Azure Portal, find your VM
- Copy the "Public IP address" (e.g., 20.123.45.67)

**Connect via SSH:**

**On Linux/Mac:**
```bash
# Save the key file
mv ~/Downloads/mrosupply-vm-key.pem ~/.ssh/
chmod 600 ~/.ssh/mrosupply-vm-key.pem

# Connect
ssh -i ~/.ssh/mrosupply-vm-key.pem azureuser@20.123.45.67
```

**On Windows (PowerShell):**
```powershell
# Save key to: C:\Users\YourName\.ssh\mrosupply-vm-key.pem

# Connect
ssh -i C:\Users\YourName\.ssh\mrosupply-vm-key.pem azureuser@20.123.45.67
```

**First time:** Type "yes" to accept fingerprint

#### Step 4: Transfer Files to Azure VM

**From your laptop:**

**Linux/Mac:**
```bash
cd /home/user/Desktop/mrosupply.com

# Transfer all files
rsync -avz -e "ssh -i ~/.ssh/mrosupply-vm-key.pem" \
  . azureuser@20.123.45.67:/tmp/mrosupply-scraper/
```

**Windows (PowerShell with SCP):**
```powershell
cd C:\Users\YourName\Desktop\mrosupply.com

# Transfer
scp -i C:\Users\YourName\.ssh\mrosupply-vm-key.pem -r * azureuser@20.123.45.67:/tmp/mrosupply-scraper/
```

**Alternative: Using Git (if you setup GitHub):**
```bash
# On Azure VM
ssh -i ~/.ssh/mrosupply-vm-key.pem azureuser@20.123.45.67

# Clone repo
cd /tmp
git clone https://github.com/YOUR_USERNAME/mrosupply-scraper.git
```

#### Step 5: Install Scraper on Azure VM

**SSH into VM:**
```bash
ssh -i ~/.ssh/mrosupply-vm-key.pem azureuser@20.123.45.67
```

**Run installation:**
```bash
# Navigate to files
cd /tmp/mrosupply-scraper

# Run setup script
sudo bash deployment/setup.sh
```

**Setup will:**
- ✅ Update system packages
- ✅ Install Python 3.10+
- ✅ Create scraper user
- ✅ Setup virtual environment
- ✅ Install dependencies
- ✅ Configure systemd service
- ✅ Setup directories

**Takes:** 5-10 minutes

#### Step 6: Configure Environment

**Edit .env file:**
```bash
sudo nano /opt/mrosupply-scraper/.env
```

**Add your credentials:**
```bash
# Proxy Settings (Webshare)
PROXY_HOST=p.webshare.io
PROXY_PORT=10000
PROXY_USER=your_webshare_username
PROXY_PASS=your_webshare_password

# Email Settings (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=abcd efgh ijkl mnop  # Your 16-char app password
NOTIFICATION_EMAIL=your_email@gmail.com

# Dashboard
DASHBOARD_PASSWORD=your_secure_password_here
DASHBOARD_PORT=8080

# Performance (for 24-hour scrape)
WORKERS=50
DELAY=0.2
MAX_RETRIES=3
RATE_LIMIT_THRESHOLD=20
COOLDOWN_MINUTES=5
ADAPTIVE_RATE_LIMIT=True

# Paths
OUTPUT_DIR=/opt/mrosupply-scraper/data
LOG_DIR=/opt/mrosupply-scraper/logs

# Monitoring
EMAIL_ON_START=True
EMAIL_ON_COMPLETE=True
EMAIL_ON_ERROR=True
EMAIL_INTERVAL_HOURS=6

# Health Checks
DISK_SPACE_THRESHOLD_GB=10
MEMORY_THRESHOLD_MB=28000
STALE_CHECKPOINT_MINUTES=30
```

**Save:** Press Ctrl+X, then Y, then Enter

#### Step 7: Open Dashboard Port

**In Azure Portal:**
1. Go to your VM
2. Click "Networking" in left menu
3. Click "Add inbound port rule"
4. Settings:
   ```
   Source: Any
   Source port ranges: *
   Destination: Any
   Service: Custom
   Destination port ranges: 8080
   Protocol: TCP
   Action: Allow
   Priority: 310
   Name: Allow-Dashboard-8080
   ```
5. Click "Add"

**On VM (firewall):**
```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

#### Step 8: Test Email Configuration

```bash
sudo -u scraper /opt/mrosupply-scraper/venv/bin/python3 \
  /opt/mrosupply-scraper/notifier.py
```

**Expected:** You should receive a test email in 10-20 seconds

**If no email:**
- Check Gmail app password is correct
- Check spam folder
- Verify SMTP settings in .env

#### Step 9: Start the Scraper

```bash
# Enable auto-start on boot
sudo systemctl enable mrosupply-scraper

# Start the service
sudo systemctl start mrosupply-scraper

# Check status
sudo systemctl status mrosupply-scraper
```

**Should see:**
```
● mrosupply-scraper.service - MRO Supply Autonomous Web Scraper
   Loaded: loaded
   Active: active (running)
```

#### Step 10: Monitor Progress

**View Logs:**
```bash
# Real-time logs
sudo journalctl -u mrosupply-scraper -f

# Last 50 lines
sudo journalctl -u mrosupply-scraper -n 50
```

**Access Dashboard:**

**Method 1: SSH Tunnel (Secure, Recommended)**
```bash
# From your laptop
ssh -i ~/.ssh/mrosupply-vm-key.pem -L 8080:localhost:8080 azureuser@20.123.45.67

# Keep terminal open, then open browser:
http://localhost:8080
```

**Method 2: Direct Access (Less Secure)**
```
http://20.123.45.67:8080  (use your VM's public IP)
```

**Login:**
- Password: The one you set in .env (DASHBOARD_PASSWORD)

---

### Option B: Azure Container Instances (Advanced)

**Use if:** You want containerized deployment

**Cost:** ~$0.04/hour (~$30/month)

**Setup:**
1. Create Dockerfile
2. Build image
3. Push to Azure Container Registry
4. Deploy to ACI

**Guide:** See `AZURE_CONTAINER_DEPLOYMENT.md` (advanced)

---

### Option C: Azure Functions (Serverless)

**Use if:** You want serverless, pay-per-execution

**Cost:** ~$0.20/1M executions + storage

**Setup:**
1. Create Function App
2. Deploy functions
3. Setup Queue Storage
4. Configure triggers

**Guide:** See `AZURE_FUNCTIONS_DEPLOYMENT.md` (advanced)

---

## Part 4: Cost Management 💰

### Azure VM Costs

**Standard_D8s_v3 (8 cores, 32GB):**
- **Hourly:** $0.38
- **Daily:** $9.12
- **For 24 hours:** $9.12
- **Monthly:** $274 (if kept running)

**With Free Credit:**
- New users: $200 free credit
- Can run: 22 days for FREE
- Or: Multiple full scrapes

### How to Minimize Costs

1. **Stop VM when not scraping:**
   ```bash
   # From Azure Portal
   VM → Stop

   # Or from CLI
   az vm stop --resource-group mrosupply-scraper-rg --name mrosupply-scraper-vm
   az vm deallocate --resource-group mrosupply-scraper-rg --name mrosupply-scraper-vm
   ```

2. **Delete when done:**
   ```bash
   # Delete entire resource group (VM + all resources)
   az group delete --name mrosupply-scraper-rg --yes
   ```

3. **Use auto-shutdown:**
   - Already configured during setup
   - VM stops automatically at 2 AM

4. **Download results before deleting:**
   ```bash
   # From your laptop
   scp -i ~/.ssh/mrosupply-vm-key.pem \
     azureuser@20.123.45.67:/opt/mrosupply-scraper/data/* \
     ./results/
   ```

### Total Cost Estimate (24-Hour Scrape)

```
Azure VM (24 hours): $9.12
Proxy (Webshare): $25.00
Total: $34.12

With free credit: $9.12 (proxy only) or $0 (use free credit)
```

---

## Part 5: Monitoring & Management 📊

### Check Scraper Status

**SSH to VM:**
```bash
ssh -i ~/.ssh/mrosupply-vm-key.pem azureuser@20.123.45.67
```

**Quick checks:**
```bash
# Service status
sudo systemctl status mrosupply-scraper

# Recent logs
sudo journalctl -u mrosupply-scraper -n 50

# Live logs
sudo journalctl -u mrosupply-scraper -f

# Check progress
sudo ls -lh /opt/mrosupply-scraper/data/checkpoint_products.json

# Count products
sudo -u scraper python3 -c "import json; print(len(json.load(open('/opt/mrosupply-scraper/data/checkpoint_products.json'))))"
```

### Email Notifications

You'll automatically receive emails for:
- ✅ Scraper started (startup notification)
- 📊 Progress updates (every 6 hours)
- ✅ Scraper completed (final summary)
- ⚠️ Warnings (disk low, memory high, etc.)
- 🚨 Critical alerts (crashes, failures)

### Dashboard Access

**From anywhere:**
```bash
# Create SSH tunnel
ssh -i ~/.ssh/mrosupply-vm-key.pem -L 8080:localhost:8080 azureuser@20.123.45.67

# Open browser: http://localhost:8080
```

**Dashboard shows:**
- Real-time progress bar
- Success rate
- Current speed
- System resources (CPU, memory, disk)
- Recent products
- Recent errors
- Charts and graphs

### Stop Scraper

```bash
# SSH to VM
ssh -i ~/.ssh/mrosupply-vm-key.pem azureuser@20.123.45.67

# Stop service
sudo systemctl stop mrosupply-scraper
```

### Restart Scraper

```bash
sudo systemctl restart mrosupply-scraper
```

---

## Part 6: Download Results 📥

### After Scraping Completes

**From your laptop:**
```bash
# Create results directory
mkdir -p ~/mrosupply-results

# Download all data files
scp -i ~/.ssh/mrosupply-vm-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/data/checkpoint_products.json \
  ~/mrosupply-results/

scp -i ~/.ssh/mrosupply-vm-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/data/products.csv \
  ~/mrosupply-results/

scp -i ~/.ssh/mrosupply-vm-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/data/failed_urls.json \
  ~/mrosupply-results/

# Download logs (optional)
scp -i ~/.ssh/mrosupply-vm-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/logs/*.log \
  ~/mrosupply-results/logs/
```

**Or download entire directory:**
```bash
scp -r -i ~/.ssh/mrosupply-vm-key.pem \
  azureuser@20.123.45.67:/opt/mrosupply-scraper/data/ \
  ~/mrosupply-results/
```

---

## Part 7: Cleanup & Cost Savings 🧹

### After Scraping is Complete

**1. Stop the VM (keeps it for later):**
```bash
# From Azure Portal
Go to VM → Click "Stop"

# Or from CLI
az vm stop --resource-group mrosupply-scraper-rg --name mrosupply-scraper-vm
az vm deallocate --resource-group mrosupply-scraper-rg --name mrosupply-scraper-vm
```
**Cost when stopped:** Only disk storage (~$5/month)

**2. Delete everything (saves maximum):**
```bash
# From Azure Portal
Go to Resource Group "mrosupply-scraper-rg" → Delete resource group

# Or from CLI
az group delete --name mrosupply-scraper-rg --yes --no-wait
```
**Cost after deletion:** $0

---

## Troubleshooting 🔧

### Email Not Working

**Check app password:**
```bash
sudo nano /opt/mrosupply-scraper/.env
# Verify SMTP_PASS has the 16-char app password (no spaces)
```

**Test manually:**
```bash
sudo -u scraper /opt/mrosupply-scraper/venv/bin/python3 /opt/mrosupply-scraper/notifier.py
```

**Common issues:**
- App password has spaces (remove them)
- 2-Step Verification not enabled
- Using regular password instead of app password
- Check spam folder

### Scraper Not Starting

**Check logs:**
```bash
sudo journalctl -u mrosupply-scraper -n 100
```

**Common issues:**
- Missing .env file
- Invalid proxy credentials
- Permissions error
- Python dependencies not installed

**Fix:**
```bash
# Reinstall
cd /tmp/mrosupply-scraper
sudo bash deployment/setup.sh

# Reconfigure
sudo nano /opt/mrosupply-scraper/.env

# Restart
sudo systemctl restart mrosupply-scraper
```

### Dashboard Not Accessible

**Check if service is running:**
```bash
sudo systemctl status mrosupply-scraper
```

**Check port 8080 is open:**
```bash
sudo netstat -tlnp | grep 8080
```

**Check Azure firewall:**
- Azure Portal → VM → Networking
- Verify port 8080 rule exists

**Access via SSH tunnel (always works):**
```bash
ssh -i ~/.ssh/mrosupply-vm-key.pem -L 8080:localhost:8080 azureuser@20.123.45.67
```

### High Costs

**If seeing unexpected charges:**

1. **Check VM is stopped:**
   - Azure Portal → VM → Status should be "Stopped (deallocated)"

2. **Check running resources:**
   ```bash
   az resource list --resource-group mrosupply-scraper-rg
   ```

3. **Set spending limit:**
   - Azure Portal → Cost Management → Budgets
   - Create budget alert at $50

---

## Quick Start Checklist ✅

### Before Starting:
- [ ] Gmail account ready
- [ ] 2-Step Verification enabled on Gmail
- [ ] App password generated (16 characters)
- [ ] Azure account created ($200 free credit)
- [ ] Credit card added to Azure (for verification)
- [ ] Webshare proxy credentials ready

### Setup (30 minutes):
- [ ] Create Azure VM (Standard_D8s_v3)
- [ ] Download SSH key
- [ ] Connect to VM via SSH
- [ ] Transfer scraper files
- [ ] Run deployment/setup.sh
- [ ] Configure .env with credentials
- [ ] Test email notifications
- [ ] Open port 8080 in Azure
- [ ] Start scraper service

### Monitoring:
- [ ] Check startup email received
- [ ] Access dashboard (SSH tunnel)
- [ ] Verify first products scraping
- [ ] Check logs for errors
- [ ] Confirm progress emails (every 6 hours)

### After Completion:
- [ ] Check completion email
- [ ] Download results files
- [ ] Stop or delete Azure VM
- [ ] Verify no charges

---

## Summary 📋

### What You Need:

**Email (5 minutes):**
- Gmail account
- Enable 2-Step Verification
- Generate app password
- Save: SMTP_USER, SMTP_PASS

**GitHub (10 minutes - OPTIONAL):**
- Create account
- Create repository
- Push code
- Add secrets

**Azure (20 minutes):**
- Create account
- Create VM (Standard_D8s_v3)
- Connect via SSH
- Deploy scraper
- Configure .env
- Start service

**Total Time:** 30-40 minutes
**Total Cost:** $34.12 (or FREE with $200 credit)

---

## Next Steps 🚀

1. **Read this guide completely**
2. **Setup Gmail app password**
3. **Create Azure account**
4. **Create Azure VM**
5. **Deploy scraper (deployment/setup.sh)**
6. **Configure .env**
7. **Start scraping**
8. **Monitor via dashboard & emails**

**Everything is automated after you start!**

---

Ready to start? Follow Part 1 (Email Setup) first! 📧
