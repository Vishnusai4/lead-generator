# Zendesk Lead Generator - Operational Runbook

**Complete operational guide for running and maintaining the lead generation pipeline.**

## Table of Contents

- [Daily Operations](#daily-operations)
- [Common Tasks](#common-tasks)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Scaling](#scaling)

---

## Daily Operations

### Morning Routine

```bash
# 1. Check system health
curl http://localhost:8000/health

# 2. Check database stats
curl http://localhost:8000/stats

# 3. Review logs for errors
tail -n 100 pipeline.log | grep ERROR

# 4. Check blocked domains
curl http://localhost:8000/blocked | jq length
```

### Running Detection

```bash
# Process new domains from CSV
python run_pipeline.py --input new_domains.csv

# With optimal settings for speed
python run_pipeline.py --input new_domains.csv \
  --threads 5 \
  --rate-limit 2.0 \
  --no-enrichment

# With enrichment and filtering
python run_pipeline.py --input new_domains.csv \
  --us-only \
  --threads 3
```

### Exporting Results

```bash
# Export from database to CSV
python -c "
from storage import LeadStorage
storage = LeadStorage()
storage.export_to_csv('daily_export.csv', detected_only=True, us_only=True)
print('Exported successfully')
"

# Or use SQLite directly
sqlite3 leads.db "SELECT * FROM leads WHERE detected_zendesk = 1" \
  -csv -header > detected_leads.csv
```

---

## Common Tasks

### Task 1: Add New Domains

```bash
# Create CSV with domains
cat > domains.csv << EOF
domain
shopify.com
stripe.com
slack.com
EOF

# Run detection
python run_pipeline.py --input domains.csv
```

### Task 2: Re-check Blocked Domains

```bash
# Export blocked domains
curl http://localhost:8000/blocked | jq -r '.[].domain' > blocked.csv

# Add header
echo "domain" | cat - blocked.csv > temp && mv temp blocked.csv

# Re-check with Playwright
python run_pipeline.py --input blocked.csv --use-playwright
```

### Task 3: Bulk Enrichment

```bash
# Get all un-enriched domains
sqlite3 leads.db \
  "SELECT domain FROM leads WHERE enriched_at IS NULL" \
  -csv -header > unenriched.csv

# Run enrichment
python run_pipeline.py --input unenriched.csv --threads 5
```

### Task 4: Query Database

```bash
# Get all detected US companies
sqlite3 leads.db << EOF
SELECT
  company_name,
  domain,
  zendesk_score,
  industry,
  employees
FROM leads
WHERE detected_zendesk = 1
  AND country = 'United States'
ORDER BY zendesk_score DESC
LIMIT 50;
EOF

# Export to CSV
sqlite3 leads.db \
  -csv -header \
  "SELECT * FROM leads WHERE detected_zendesk = 1" \
  > zendesk_companies.csv
```

### Task 5: API Queries

```bash
# Get statistics
curl http://localhost:8000/stats | jq

# Get top detected companies (with pagination)
curl "http://localhost:8000/leads?detected_only=true&limit=50" | jq

# Search specific domain
curl http://localhost:8000/lead/shopify.com | jq

# Trigger detection via API
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "enrich": true}' | jq
```

---

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00.000Z",
  "version": "1.0.0",
  "components": {
    "detector": "ok",
    "enricher": "ok",
    "storage": "ok",
    "database": "ok"
  }
}
```

### Log Monitoring

```bash
# Watch logs in real-time
tail -f pipeline.log

# Filter for errors
tail -f pipeline.log | grep ERROR

# Count blocking events today
grep "BLOCKED" pipeline.log | grep "$(date +%Y-%m-%d)" | wc -l

# View structured blocking events
grep "blocked_by_waf" pipeline.log | tail -n 10
```

### Database Monitoring

```bash
# Check database size
ls -lh leads.db

# Count records
sqlite3 leads.db "SELECT COUNT(*) FROM leads"

# Detection rate
sqlite3 leads.db << EOF
SELECT
  COUNT(*) as total,
  SUM(detected_zendesk) as detected,
  ROUND(SUM(detected_zendesk) * 100.0 / COUNT(*), 2) as detection_rate
FROM leads;
EOF

# Enrichment rate
sqlite3 leads.db << EOF
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN enriched_at IS NOT NULL THEN 1 ELSE 0 END) as enriched,
  ROUND(SUM(CASE WHEN enriched_at IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as enrichment_rate
FROM leads;
EOF
```

### Performance Metrics

```bash
# Pipeline throughput
time python run_pipeline.py --input test_domains.csv

# Database query performance
time sqlite3 leads.db "SELECT * FROM leads WHERE detected_zendesk = 1"

# API response time
time curl http://localhost:8000/leads > /dev/null
```

---

## Troubleshooting

### Issue: 403 Forbidden Errors

**Symptoms:** Most domains return 403 status

**Solution:**
```bash
# Enable cloudscraper
python run_pipeline.py --use-cloudscraper --input domains.csv

# Or use Playwright
python run_pipeline.py --use-playwright --input domains.csv

# Check specific domain with verbose logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from detect_zendesk import ZendeskDetector
detector = ZendeskDetector(use_playwright=True)
result = detector.detect('example.com')
print(result)
"
```

### Issue: Playwright Not Working

**Symptoms:** "Playwright not available" errors

**Solution:**
```bash
# Install Playwright
pip install playwright

# Install browsers
playwright install chromium

# Install system dependencies (Linux)
playwright install-deps chromium

# Test Playwright
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    print('Playwright working!')
    browser.close()
"
```

### Issue: Database Locked

**Symptoms:** "database is locked" error

**Solution:**
```bash
# Check for open connections
lsof leads.db

# Close API server if running
pkill -f "python api.py"

# Or use different database
python run_pipeline.py --db-path leads2.db
```

### Issue: Slow Performance

**Symptoms:** Pipeline taking too long

**Solution:**
```bash
# Disable enrichment
python run_pipeline.py --no-enrichment --input domains.csv

# Increase threads
python run_pipeline.py --threads 10 --input domains.csv

# Increase rate limit
python run_pipeline.py --rate-limit 2.0 --input domains.csv

# Check network latency
ping google.com
```

### Issue: Out of Memory

**Symptoms:** Process killed or memory errors

**Solution:**
```bash
# Process in smaller batches
split -l 100 large_domains.csv batch_

# Process each batch
for file in batch_*; do
  python run_pipeline.py --input "$file"
done

# Reduce threads
python run_pipeline.py --threads 1 --input domains.csv
```

---

## Maintenance

### Daily Maintenance

```bash
# Backup database
cp leads.db "backups/leads_$(date +%Y%m%d).db"

# Export CSV
python -c "
from storage import LeadStorage
storage = LeadStorage()
storage.export_to_csv()
"

# Clean old logs (keep 30 days)
find . -name "*.log" -mtime +30 -delete

# Check disk space
df -h .
```

### Weekly Maintenance

```bash
# Vacuum database
sqlite3 leads.db "VACUUM;"

# Check database integrity
sqlite3 leads.db "PRAGMA integrity_check;"

# Update dependencies
pip list --outdated

# Run test suite
pytest test_pipeline.py -v

# Review blocked domains
curl http://localhost:8000/blocked | jq -r '.[].domain' > blocked_review.txt
```

### Monthly Maintenance

```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Update Playwright
playwright install chromium

# Archive old data
sqlite3 leads.db << EOF
CREATE TABLE IF NOT EXISTS leads_archive AS
SELECT * FROM leads WHERE created_at < date('now', '-90 days');

DELETE FROM leads WHERE created_at < date('now', '-90 days');
EOF

# Generate monthly report
sqlite3 leads.db << EOF
SELECT
  DATE(created_at) as date,
  COUNT(*) as total,
  SUM(detected_zendesk) as detected
FROM leads
WHERE created_at >= date('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
EOF
```

---

## Scaling

### Horizontal Scaling

```bash
# Run multiple instances with different input files
python run_pipeline.py --input batch1.csv --db-path db1.db &
python run_pipeline.py --input batch2.csv --db-path db2.db &
python run_pipeline.py --input batch3.csv --db-path db3.db &

# Wait for completion
wait

# Merge databases
sqlite3 leads_merged.db << EOF
ATTACH 'db1.db' AS db1;
ATTACH 'db2.db' AS db2;
ATTACH 'db3.db' AS db3;

INSERT OR IGNORE INTO leads SELECT * FROM db1.leads;
INSERT OR IGNORE INTO leads SELECT * FROM db2.leads;
INSERT OR IGNORE INTO leads SELECT * FROM db3.leads;
EOF
```

### Vertical Scaling

```bash
# Increase threads for CPU-bound tasks
python run_pipeline.py --threads 20 --input domains.csv

# Increase rate limit for I/O-bound tasks
python run_pipeline.py --rate-limit 5.0 --input domains.csv

# Use faster detection (no escalation)
python run_pipeline.py --no-escalation --input domains.csv
```

### Cloud Deployment

```bash
# Deploy on AWS/GCP/Azure

# 1. Build Docker image
docker build -t zendesk-lead-generator .

# 2. Push to container registry
docker tag zendesk-lead-generator gcr.io/my-project/lead-generator
docker push gcr.io/my-project/lead-generator

# 3. Deploy to Cloud Run / ECS / App Engine
gcloud run deploy lead-generator \
  --image gcr.io/my-project/lead-generator \
  --platform managed \
  --port 8000 \
  --set-env-vars CLEARBIT_API_KEY=xxx

# 4. Access deployed service
curl https://lead-generator-xxx.run.app/health
```

---

## Automation

### Cron Jobs (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add daily job at 2 AM
0 2 * * * cd /path/to/lead-generator && python run_pipeline.py --input daily.csv

# Add weekly backup at Sunday 3 AM
0 3 * * 0 cd /path/to/lead-generator && cp leads.db "backups/leads_$(date +\%Y\%m\%d).db"

# Add hourly health check
0 * * * * curl http://localhost:8000/health || echo "API down" | mail -s "Alert" admin@example.com
```

### Task Scheduler (Windows)

```powershell
# Create scheduled task
schtasks /create /tn "ZendeskLeadGen" /tr "python C:\path\to\run_pipeline.py" /sc daily /st 02:00

# Run on system startup
schtasks /create /tn "ZendeskAPI" /tr "python C:\path\to\api.py" /sc onstart
```

---

## Best Practices

1. **Always backup** before major operations
2. **Monitor logs** for blocking patterns
3. **Respect rate limits** - default 1 req/sec
4. **Use Playwright sparingly** - only when needed
5. **Export regularly** - CSV backups daily
6. **Test in batches** - small test before large runs
7. **Check compliance** - respect robots.txt
8. **Rotate proxies** - if using proxy-file
9. **Update regularly** - dependencies and browsers
10. **Document changes** - maintain operations log

---

## Emergency Procedures

### Database Corruption

```bash
# 1. Stop all processes
pkill -f run_pipeline
pkill -f api.py

# 2. Backup corrupted database
cp leads.db leads_corrupted_$(date +%Y%m%d).db

# 3. Try to recover
sqlite3 leads.db "PRAGMA integrity_check;"

# 4. If recovery fails, restore from backup
cp backups/leads_latest.db leads.db

# 5. Verify restoration
sqlite3 leads.db "SELECT COUNT(*) FROM leads;"
```

### API Down

```bash
# 1. Check if process running
ps aux | grep api.py

# 2. Check port
lsof -i :8000

# 3. Restart API
pkill -f api.py
python api.py &

# 4. Verify
curl http://localhost:8000/health
```

### Disk Full

```bash
# 1. Check disk usage
df -h

# 2. Clean logs
rm -f *.log

# 3. Vacuum database
sqlite3 leads.db "VACUUM;"

# 4. Archive old data
# (See Monthly Maintenance section)

# 5. Compress old backups
gzip backups/*.db
```

---

## Support Contacts

- **Technical Issues**: tech@example.com
- **API Documentation**: http://localhost:8000/docs
- **GitHub Issues**: https://github.com/Vishnusai4/lead-generator/issues

---

**Last Updated:** 2025-01-10
