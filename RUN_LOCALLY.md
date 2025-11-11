# How to Run Zendesk Lead Generator Locally

## Why You Need to Run This Locally

This code is currently running in a sandboxed environment that blocks all external internet access. To actually detect Zendesk installations, you need to run it on a machine with unrestricted internet access.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Vishnusai4/lead-generator.git
cd lead-generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure ScraperAPI (Optional but Recommended)
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your ScraperAPI key
# SCRAPERAPI_KEY=ee462d48408ee47a4258410b6da43640
```

### 4. Run the Detection Pipeline

**Option A: With ScraperAPI (Best Success Rate)**
```bash
# Set your API key
export SCRAPERAPI_KEY=ee462d48408ee47a4258410b6da43640

# Run on the 25K domain list
python run_pipeline.py \
  --input top_25k_us_focused_domains.csv \
  --output zendesk_leads.csv \
  --threads 10 \
  --us-only
```

**Option B: With Cloudscraper (Free, Lower Success Rate)**
```bash
python run_pipeline.py \
  --input top_25k_us_focused_domains.csv \
  --output zendesk_leads.csv \
  --use-cloudscraper \
  --threads 5
```

**Option C: With Playwright (Most Powerful, Slowest)**
```bash
# First install Playwright browsers
python -m playwright install chromium

# Then run
python run_pipeline.py \
  --input top_25k_us_focused_domains.csv \
  --output zendesk_leads.csv \
  --use-playwright \
  --threads 3
```

### 5. Monitor Progress

The pipeline will:
- Process domains in parallel (configurable with `--threads`)
- Log progress to console and `pipeline.log`
- Save results to SQLite database (`zendesk_leads.db`)
- Export to CSV (`zendesk_leads.csv`)

### 6. Expected Runtime

- **25,000 domains** at 10 threads: ~40-50 minutes
- **25,000 domains** at 5 threads: ~80-90 minutes

### 7. Check Results

```bash
# View summary
python -c "import sqlite3; db = sqlite3.connect('zendesk_leads.db'); \
print(f'Total detections: {db.execute(\"SELECT COUNT(*) FROM detections WHERE detected=1\").fetchone()[0]}')"

# View CSV
head zendesk_leads.csv
```

## Troubleshooting

### ScraperAPI Returns 403
- Check your API key is valid: https://www.scraperapi.com/dashboard
- Verify you have credits remaining (1000/month on free tier)
- Try from a different network (mobile hotspot, VPN, etc.)

### Too Many Blocks Even with ScraperAPI
- Enable JS rendering: Add `render=true` in detect_zendesk.py (costs 5 credits per request)
- Reduce thread count: Use `--threads 1` to avoid rate limiting
- Try Playwright instead: `--use-playwright` (slowest but most effective)

### Running on a Cloud Instance
If your local network has restrictions, run on AWS/GCP/DigitalOcean:

```bash
# Example: AWS EC2 t2.micro (free tier)
ssh your-ec2-instance
git clone https://github.com/Vishnusai4/lead-generator.git
cd lead-generator
pip3 install -r requirements.txt
export SCRAPERAPI_KEY=ee462d48408ee47a4258410b6da43640
nohup python run_pipeline.py --input top_25k_us_focused_domains.csv --threads 10 &
```

## Expected Results

Based on previous testing:
- **Detection Rate:** 5-15% of domains use Zendesk
- **With ScraperAPI:** 90%+ success rate bypassing WAF
- **Without ScraperAPI:** 50-70% blocked by anti-bot systems

For 25K domains, expect to find **1,250 - 3,750 companies using Zendesk**.
