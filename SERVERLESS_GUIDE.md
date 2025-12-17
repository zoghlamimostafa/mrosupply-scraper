# Serverless Scraping Guide
## GitHub Actions + Azure Functions

This guide covers two serverless approaches for distributed scraping.

---

## Overview

### Why Serverless?

**Pros:**
- ✅ No server management
- ✅ Automatic scaling
- ✅ Pay per use (potentially cheaper)
- ✅ Built-in redundancy
- ✅ Distributed execution
- ✅ Easy to pause/resume

**Cons:**
- ❌ Execution time limits (GitHub: 6h, Azure: 10min default)
- ❌ More complex orchestration
- ❌ Potential cold start delays
- ❌ Network egress costs
- ❌ Harder to debug

---

## Method 1: GitHub Actions

### How It Works

1. Split 1.5M URLs into batches (e.g., 500 URLs each = 3,000 batches)
2. Use GitHub Actions matrix strategy to run 256 jobs in parallel
3. Each job processes one batch
4. Upload results to GitHub artifacts or Azure Blob Storage

### Advantages
- Free tier: 2,000 minutes/month (private repos) or unlimited (public repos)
- Can run up to 256 concurrent jobs
- 6-hour timeout per job
- Good for CPU-bound tasks

### Limitations
- 2,000 minutes/month limit (private repos)
- 6-hour max execution per job
- 10GB artifact storage
- Need to manage job coordination

### Cost Estimate

**For public repository:** FREE (unlimited minutes)

**For private repository:**
- Free tier: 2,000 minutes/month
- 1.5M products ÷ 500 per job = 3,000 jobs
- At ~10 min/job = 30,000 minutes needed
- Overage: (30,000 - 2,000) × $0.008/min = $224

**Recommendation:** Use public repository or GitHub Actions + paid plan ($4/month for 3,000 minutes)

---

## Method 2: Azure Functions

### How It Works

1. HTTP-triggered or Queue-triggered functions
2. Process URLs from Azure Queue Storage
3. Store results in Azure Blob Storage
4. Use Durable Functions for orchestration

### Advantages
- Auto-scaling to hundreds of instances
- Better for I/O-bound tasks (web scraping)
- Integration with Azure services
- No arbitrary timeout with Durable Functions

### Limitations
- Cold start delays (1-3 seconds)
- Execution time limits (Consumption plan: 5-10 min)
- Network egress costs
- More expensive than GitHub Actions

### Cost Estimate

**Azure Functions (Consumption Plan):**
- Execution: $0.20 per 1M executions
- Duration: $0.000016 per GB-second
- Storage: $0.018 per GB/month

**Example for 1.5M products:**
- Executions: 1.5M × $0.20/1M = $0.30
- Duration: 1.5M × 2s × 0.5GB × $0.000016 = $24
- Storage: 10GB × $0.018 = $0.18/month
- Egress: 75GB × $0.087 = $6.53
- **Total: ~$31**

---

## Method 3: Hybrid (GitHub Actions as Orchestrator)

### Architecture

```
GitHub Actions (Free Orchestrator)
    ↓
Splits URLs into batches
    ↓
Triggers Azure Functions (Workers)
    ↓
Results → Azure Blob Storage
    ↓
GitHub Actions (Aggregator) → Final CSV
```

### Advantages
- Free orchestration (GitHub Actions)
- Scalable execution (Azure Functions)
- Best of both worlds
- Lower cost than pure Azure

### Cost Estimate
- GitHub Actions: Free (orchestration only)
- Azure Functions: ~$20 (reduced load)
- **Total: ~$20**

---

## Implementation Files

### 1. Split URLs Script
File: `serverless/split_urls.py`
- Splits 1.5M URLs into manageable batches
- Creates batch files for parallel processing

### 2. GitHub Actions Workflow
File: `.github/workflows/scrape.yml`
- Matrix strategy for parallel execution
- Handles 256 concurrent jobs
- Uploads results to artifacts

### 3. Azure Function
File: `serverless/azure_function/`
- HTTP-triggered scraper function
- Queue-triggered worker function
- Blob storage integration

### 4. Orchestrator
File: `serverless/orchestrator.py`
- Coordinates batch processing
- Monitors progress
- Handles failures and retries

---

## Recommended Approach

### For Budget-Conscious ($0-5):
**GitHub Actions (Public Repo)**
- Make repo public
- Unlimited minutes
- 256 parallel jobs
- Complete in 2-3 hours
- Cost: $0

### For Speed (24 hours):
**Dedicated Server (Hetzner)**
- 50 workers
- Complete in 24 hours
- Full control
- Cost: $1.50

### For Scalability:
**Hybrid (GitHub + Azure)**
- GitHub orchestration (free)
- Azure execution (scalable)
- Complete in 1-2 hours
- Cost: $20

---

## Performance Comparison

| Method | Time | Cost | Setup | Control |
|--------|------|------|-------|---------|
| Dedicated Server | 24h | $1.50 | Easy | Full |
| GitHub Actions | 2-3h | $0-224 | Medium | Limited |
| Azure Functions | 1-2h | $31 | Complex | Medium |
| Hybrid | 1-2h | $20 | Complex | Medium |

---

## Next Steps

Choose your approach:

1. **Traditional Server (Recommended)**
   - Read: `SERVER_REQUIREMENTS.md`
   - Deploy: `deployment/setup.sh`
   - Cost: $1.50/day

2. **GitHub Actions**
   - Read: `serverless/GITHUB_ACTIONS.md`
   - Setup: `.github/workflows/scrape.yml`
   - Cost: Free (public) or $4/month

3. **Azure Functions**
   - Read: `serverless/AZURE_FUNCTIONS.md`
   - Deploy: `serverless/deploy_azure.sh`
   - Cost: ~$31

4. **Hybrid**
   - Read: `serverless/HYBRID_APPROACH.md`
   - Setup: Both GitHub + Azure
   - Cost: ~$20

---

## Implementation Priority

Based on your needs, I recommend:

### Best Overall: Traditional Server + GitHub Actions Backup
- **Primary:** Hetzner server ($1.50/day) for 24h scrape
- **Backup:** GitHub Actions workflow ready if server fails
- **Total cost:** $1.50
- **Completion:** 24 hours guaranteed

I can implement either approach. Which would you prefer?
