# Zendesk Lead Generator

**Production-ready pipeline for detecting Zendesk usage and enriching company data.**

Automatically identifies companies using Zendesk through multi-tier detection with bot-blocking resistance, enriches with company intelligence, and stores in SQLite + CSV with REST API access.

> **⚠️ IMPORTANT:** This tool requires unrestricted internet access to scrape websites. If running in a sandboxed environment (Docker container, CI/CD, etc.), you may encounter network restrictions. **See [RUN_LOCALLY.md](RUN_LOCALLY.md) for setup instructions.**

## Features

### 🔍 Multi-Tier Detection
- **Fast HTML check** - Quick detection using requests
- **ScraperAPI integration** - Professional anti-bot bypass (90%+ success rate)
- **Cloudflare bypass** - Automatic escalation with cloudscraper
- **Playwright fallback** - Full browser automation for JavaScript-heavy sites
- **Automatic escalation** - Smart handling of bot-blocking (403/406/429/503)
- **Signal-based scoring** - Weighted detection with configurable thresholds

### 💰 Company Enrichment
- **Clearbit integration** - Premium company data (employees, industry, location)
- **Free fallback** - Web scraping when Clearbit unavailable
- **US filtering** - Automatic filtering for US-based companies
- **LinkedIn discovery** - Company profile URLs
- **Pluggable providers** - Easy to add new data sources

### 💾 Dual Persistence
- **SQLite database** - Fast queries and filtering
- **CSV export** - Easy sharing and analysis
- **Automatic deduplication** - No duplicate domains
- **Blocking metadata** - Track WAF blocks and status codes

### 🚀 REST API
- **FastAPI server** - Modern async Python API
- **Interactive docs** - Swagger UI at /docs
- **Health checks** - Monitor system status
- **Batch operations** - Process multiple domains
- **Filtering** - Query by detection status, country, etc.

### 🐳 Production Ready
- **Docker deployment** - Single command setup
- **Multi-threading** - Concurrent processing
- **Rate limiting** - Respectful scraping
- **Comprehensive logging** - Structured JSON logs
- **Error handling** - Graceful degradation
- **Test suite** - Unit and integration tests

## Quick Start

### Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/Vishnusai4/lead-generator.git
cd lead-generator

# 2. Configure environment (optional)
echo "CLEARBIT_API_KEY=your_key_here" > .env

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access API
curl http://localhost:8000/health
open http://localhost:8000/docs
```

### Local Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Run detection pipeline
python run_pipeline.py --input examples/seed.csv

# 4. Start API server
python api.py
```

## Usage

### CLI - Detection Pipeline

```bash
# Basic detection
python run_pipeline.py --input domains.csv

# With enrichment and US-only filter
python run_pipeline.py --input domains.csv --us-only

# Force Playwright for all domains
python run_pipeline.py --input domains.csv --use-playwright

# Multi-threaded processing
python run_pipeline.py --input domains.csv --threads 10

# Detection only (no enrichment)
python run_pipeline.py --input domains.csv --no-enrichment
```

**Available Flags:**
- `--input` - Input CSV with domain column (default: examples/seed.csv)
- `--output` - Output CSV path (default: leads.csv)
- `--db-path` - SQLite database path (default: leads.db)
- `--threads` - Concurrent threads (default: 1)
- `--use-cloudscraper` - Enable Cloudflare bypass
- `--use-playwright` - Force browser automation
- `--no-escalation` - Disable automatic escalation
- `--us-only` - Only process US companies (default: True)
- `--no-enrichment` - Skip enrichment
- `--rate-limit` - Requests per second (default: 1.0)

### REST API

Start the API server:

```bash
python api.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Endpoints:**

```bash
# Health check
curl http://localhost:8000/health

# Detect Zendesk for a domain
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"domain": "shopify.com", "enrich": true}'

# Get all leads
curl http://localhost:8000/leads

# Get detected leads only
curl http://localhost:8000/leads?detected_only=true

# Get US companies only
curl http://localhost:8000/leads?us_only=true

# Get specific lead
curl http://localhost:8000/lead/shopify.com

# Get statistics
curl http://localhost:8000/stats

# Get blocked leads
curl http://localhost:8000/blocked
```

## Configuration

### Detection Settings (`config.yaml`)

```yaml
detection:
  weights:
    script_zendesk: 60       # Zendesk script tag
    cdn_zdassets: 60         # Zendesk CDN
    help_subdomain_link: 80  # help.*.zendesk.com link
    window_ze: 120           # window.zE global
    window_zendesk: 120      # window.Zendesk global
    xhr_zendesk: 100         # XHR to zendesk.com
  threshold: 100             # Minimum score for detection
  cache_days: 30             # Cache duration
```

### Environment Variables (`.env`)

```bash
# Anti-Bot Bypass (RECOMMENDED)
SCRAPERAPI_KEY=your_scraperapi_key_here  # Get free key at https://www.scraperapi.com/

# Enrichment API Keys (optional)
CLEARBIT_API_KEY=your_clearbit_api_key_here

# Database
DATABASE_URL=sqlite:///leads.db

# Logging
LOG_LEVEL=INFO

# API
API_PORT=8000
```

**ScraperAPI Setup (Recommended for 90%+ Success Rate):**
1. Sign up at https://www.scraperapi.com/ (FREE - 1,000 requests/month)
2. Copy your API key from the dashboard
3. Set environment variable: `export SCRAPERAPI_KEY=your_key`
4. Run pipeline normally - ScraperAPI will automatically activate

## Architecture

```
┌─────────────┐
│  Input CSV  │
└─────┬───────┘
      │
      v
┌─────────────────────┐
│  Detection Module   │
│  ┌───────────────┐  │
│  │ Fast Check    │──┐
│  └───────────────┘  │
│  ┌───────────────┐  │  On 403/429
│  │ ScraperAPI    │◄─┤  Escalate
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ Cloudscraper  │◄─┤
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ Playwright    │◄─┘
│  └───────────────┘  │
└─────────┬───────────┘
          │
          v
┌─────────────────────┐
│ Enrichment Module   │
│  ┌───────────────┐  │
│  │ Clearbit API  │  │
│  └───────┬───────┘  │
│          │ Fallback │
│  ┌───────v───────┐  │
│  │ Free Scraping │  │
│  └───────────────┘  │
└─────────┬───────────┘
          │
          v
┌─────────────────────┐
│   Storage Layer     │
│  ┌───────────────┐  │
│  │  SQLite DB    │  │
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │  CSV Export   │  │
│  └───────────────┘  │
└─────────┬───────────┘
          │
          v
┌─────────────────────┐
│    REST API         │
│  (FastAPI/Uvicorn)  │
└─────────────────────┘
```

## Data Schema

### SQLite / CSV Columns

| Column | Type | Description |
|--------|------|-------------|
| `domain` | TEXT | Company domain (unique) |
| `company_name` | TEXT | Company name |
| `detected_zendesk` | BOOLEAN | Zendesk detected |
| `zendesk_score` | INTEGER | Detection confidence score |
| `signals` | JSON | Detection signals found |
| `employees` | INTEGER | Employee count |
| `industry` | TEXT | Industry category |
| `country` | TEXT | Country |
| `state` | TEXT | State/province |
| `city` | TEXT | City |
| `linkedin_url` | TEXT | LinkedIn company page |
| `enriched_at` | TEXT | Enrichment timestamp |
| `detection_timestamp` | TEXT | Detection timestamp |
| `blocked_by_waf` | BOOLEAN | Blocked by WAF |
| `original_status_code` | INTEGER | HTTP status code |
| `original_headers` | TEXT | Response headers (JSON) |
| `detection_method` | TEXT | Detection method used |
| `error` | TEXT | Error message if failed |

## Testing

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest test_pipeline.py -v

# Run with coverage
pytest test_pipeline.py --cov=. --cov-report=html

# Run specific test class
pytest test_pipeline.py::TestStorage -v
```

## Deployment

### Docker Production Deployment

```bash
# Build image
docker build -t zendesk-lead-generator .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -e CLEARBIT_API_KEY=your_key \
  --name lead-generator \
  zendesk-lead-generator

# View logs
docker logs -f lead-generator

# Stop container
docker stop lead-generator
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## Legal & Compliance

### Robots.txt
By default, the pipeline respects robots.txt. Use `--ignore-robots` flag to override (not recommended).

### Rate Limiting
Default rate limit is 1 request/second. Adjust with `--rate-limit` flag.

### User Agent
Identifies as "ZendeskLeadGenerator/1.0" - be respectful of website policies.

### Data Privacy
- Only collects publicly available business information
- No personal data collection
- No authentication bypassing
- Compliant with public web scraping best practices

## Troubleshooting

### Common Issues

**Network Restrictions / Proxy Blocking**

If you see errors like `403 Forbidden` on ALL requests or `Access denied` from proxy:

```bash
# You're in a sandboxed environment - run locally instead
# See RUN_LOCALLY.md for instructions

# Quick test: Check if you can reach the internet
curl https://httpbin.org/get

# If blocked, you need to run on:
# 1. Your local machine
# 2. A cloud instance (AWS/GCP/DigitalOcean)
# 3. A different network (mobile hotspot, etc.)
```

**403 Forbidden from Target Websites**

If specific domains return 403 (anti-bot protection):

```bash
# Best: Use ScraperAPI (90%+ success rate)
export SCRAPERAPI_KEY=your_key
python run_pipeline.py --input domains.csv

# Alternative: Use cloudscraper
python run_pipeline.py --use-cloudscraper

# Last resort: Use Playwright (slowest)
python run_pipeline.py --use-playwright
```

**Playwright Installation**
```bash
# Install browsers
playwright install chromium

# Install system dependencies (Linux)
playwright install-deps
```

**Module Not Found**
```bash
# Ensure virtual environment activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Database Locked**
```bash
# Close any open connections
# Or use different database file
python run_pipeline.py --db-path leads2.db
```

## Performance

### Benchmarks
- **Fast detection**: ~1-2 seconds per domain
- **With enrichment**: ~3-5 seconds per domain
- **With Playwright**: ~10-15 seconds per domain
- **Multi-threaded**: ~100 domains in 5-10 minutes (10 threads)

### Optimization Tips
1. Use `--no-enrichment` for faster detection-only runs
2. Increase `--threads` for batch processing
3. Use `--use-cloudscraper` only when needed
4. Cache results in database to avoid re-checking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run test suite: `pytest test_pipeline.py -v`
6. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: See RUNBOOK.md for operational procedures
- **Issues**: https://github.com/Vishnusai4/lead-generator/issues
- **Email**: support@example.com

## Changelog

### Version 1.1.0 (2025-11-11)
- **ScraperAPI integration** for professional anti-bot bypass (90%+ success rate)
- 4-tier escalation: requests → ScraperAPI → cloudscraper → Playwright
- Environment testing script (`test_environment.py`)
- Local deployment guide (`RUN_LOCALLY.md`)
- Updated documentation for sandboxed environments

### Version 1.0.0 (2025-01-10)
- Production-ready pipeline with escalation
- Multi-tier detection (requests → cloudscraper → Playwright)
- Company enrichment with Clearbit + free fallback
- US-only filtering
- SQLite + CSV persistence
- REST API with FastAPI
- Docker deployment
- Comprehensive test suite
- Full documentation

---

**Built with ❤️ for lead generation teams**
