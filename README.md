# Zendesk Lead Finder

**Automated lead generation system that finds 50-100 companies using Zendesk per day and saves them to Google Sheets.**

## Overview

This system automatically identifies companies using Zendesk for customer support by:
1. Scraping G2 reviews for Zendesk
2. Scraping Zendesk's official customer showcase
3. Loading a database of 113+ known Zendesk customers
4. Enriching company data with websites and LinkedIn URLs
5. Automatically saving to Google Sheets with deduplication

**Cost: $0** - Uses only free tools and APIs

## What You Get

- **50-100 new companies daily** (when run daily)
- **1,500-3,000 companies in 30 days**
- **Automatic deduplication** - never add the same company twice
- **Enriched data** - websites and LinkedIn URLs included
- **Google Sheets integration** - easy to use and share
- **Ready for outreach** - export to your CRM or email tool

## Features

### Multi-Source Scraping
- **G2 Reviews**: Extracts companies from Zendesk reviews on G2.com
- **Zendesk Showcase**: Scrapes Zendesk's official customer pages
- **Known Customers**: Database of 113+ verified Zendesk users

### Intelligent Enrichment
- **Website Discovery**: Uses DuckDuckGo API to find company websites
- **LinkedIn URLs**: Auto-generates LinkedIn company page URLs
- **Website Validation**: Verifies websites are accessible

### Google Sheets CRM
- **Auto-Formatting**: Professional-looking headers and layout
- **17 Data Columns**: Name, website, industry, size, LinkedIn, and more
- **Duplicate Detection**: Checks both company name and website
- **Status Tracking**: Mark companies as "New", "Contacted", "Qualified", etc.

### Automation Ready
- **Daily Automation**: Set and forget with cron (Mac/Linux) or Task Scheduler (Windows)
- **Logging**: Track all runs and errors
- **Multiple Run Modes**: Test, full, G2-only, Zendesk-only

## Prerequisites

- Python 3.8 or higher
- Google account (for Google Sheets)
- Internet connection

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a 15-minute setup guide.

## Detailed Setup Instructions

### Step 1: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

**To enable APIs:**
- Click "Enable APIs and Services"
- Search for "Google Sheets API" and enable it
- Search for "Google Drive API" and enable it

### Step 3: Create Service Account

1. In Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name: `zendesk-lead-finder`
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"

### Step 4: Download Credentials

1. Click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create New Key"
4. Select "JSON" format
5. Click "Create"
6. Save the downloaded file as `credentials.json` in your project folder

**IMPORTANT**: The JSON file contains your service account email. You'll need this in the next step!

Example email: `zendesk-lead-finder@your-project.iam.gserviceaccount.com`

### Step 5: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Name it: `Teravictus Leads` (or your preferred name)
4. Click "Share" button
5. Paste your service account email (from credentials.json)
6. Give it "Editor" permissions
7. Click "Send"

### Step 6: Configure the Application

```bash
# Copy configuration template
cp config_template.py config.py

# Edit config.py with your settings
nano config.py  # or use your favorite editor
```

Update these values in `config.py`:
```python
GOOGLE_SHEETS_CREDENTIALS_PATH = "credentials.json"
GOOGLE_SHEET_NAME = "Teravictus Leads"
WORKSHEET_NAME = "Companies"
```

### Step 7: Verify Setup

```bash
python verify_setup.py
```

This will check:
- Python version
- All dependencies
- Configuration file
- Credentials file
- Google Sheets connection

**All checks must pass before proceeding!**

### Step 8: Test Run

```bash
python main.py --mode test
```

This will:
- Scrape 1 page from G2
- Scrape Zendesk showcase
- Load 5 known customers
- Enrich 3 sample companies
- Show you the data (does NOT save to sheets)

### Step 9: First Full Run

```bash
python main.py --mode full
```

This will:
- Scrape 10 pages from G2
- Scrape all Zendesk customer pages
- Load all 113 known customers
- Enrich all companies with websites/LinkedIn
- Save everything to Google Sheets
- Show you the results

**Expected time**: 10-15 minutes
**Expected results**: 50-150 companies

## Usage

### Run Modes

```bash
# Full pipeline (recommended for daily runs)
python main.py --mode full

# Test mode (quick verification)
python main.py --mode test

# G2 only
python main.py --mode g2-only

# Zendesk showcase only
python main.py --mode zendesk-only

# Skip enrichment (faster but less data)
python main.py --mode full --no-enrich
```

### Daily Automation

#### Mac/Linux (Cron)

```bash
# Make main.py executable
chmod +x main.py

# Edit crontab
crontab -e

# Add this line (runs at 9:00 AM daily)
0 9 * * * cd /path/to/lead-generator && /path/to/venv/bin/python main.py --mode full >> logs/cron.log 2>&1
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Click "Create Basic Task"
3. Name: "Zendesk Lead Finder"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py --mode full`
   - Start in: `C:\path\to\lead-generator`
6. Click "Finish"

## Google Sheets Structure

The system creates a spreadsheet with these columns:

| Column | Description |
|--------|-------------|
| Company Name | Name of the company |
| Website | Company website URL |
| Industry | Industry/vertical |
| Company Size | Small, Mid-Market, or Enterprise |
| Location | Company location |
| Description | Company description |
| LinkedIn URL | LinkedIn company page |
| Uses Zendesk | Yes/Unknown |
| Source | G2, Zendesk Showcase, or Known Customer |
| Date Added | When added to database |
| Status | New, Contacted, Qualified, etc. |
| Notes | Your notes |
| Contact Found | Yes/No |
| Contact Name | Decision maker name |
| Contact Email | Contact email |
| Contact LinkedIn | Contact's LinkedIn |
| Last Updated | Last modification date |

## Expected Results

### Daily (1 run per day)
- 50-100 new companies
- ~70% with websites
- 100% with LinkedIn URLs

### Weekly (7 runs)
- 350-700 new companies
- Large database to start outreach

### Monthly (30 runs)
- 1,500-3,000 new companies
- Extensive target list
- Ready for large-scale outreach

## Troubleshooting

### "No module named 'config'"
- You need to create `config.py` from `config_template.py`
- Run: `cp config_template.py config.py`

### "Credentials file not found"
- Download credentials.json from Google Cloud Console
- Place it in the project root directory
- Update path in `config.py`

### "Failed to connect to Google Sheets"
- Make sure you shared the sheet with your service account email
- Check that Google Sheets API and Drive API are enabled
- Verify credentials.json is valid JSON

### "No companies found"
- G2 and Zendesk may have changed their HTML structure
- Known customers will still work (113 companies)
- Check internet connection
- Try running with `--mode test` to debug

### "Website not found" for many companies
- This is normal - not all companies have easily findable websites
- The enricher makes best guesses
- You can manually add websites later in Google Sheets

## Next Steps After Building Your Database

### 1. Find Contacts (Days 1-7)

Use these tools to find decision makers:

- **Apollo.io** (free tier: 50 contacts/month)
- **Hunter.io** (free tier: 50 searches/month)
- **LinkedIn Sales Navigator** (trial available)
- **RocketReach** (free tier available)

Target roles:
- VP of Customer Success
- Head of Customer Support
- CX Director
- COO

### 2. Enrich Contacts (Days 8-14)

Add to your spreadsheet:
- Contact name
- Contact email
- Contact LinkedIn
- Contact title

### 3. Start Outreach (Days 15+)

**Email Sequences:**
- Day 1: Introduction email
- Day 4: Value proposition
- Day 7: Case study/social proof
- Day 10: Final follow-up

**LinkedIn Outreach:**
- Connect with contacts
- Engage with their content
- Send personalized messages

### 4. Track Results

Update the "Status" column:
- **New**: Just added
- **Contacted**: Outreach sent
- **Responded**: They replied
- **Qualified**: Good fit
- **Meeting Booked**: Call scheduled
- **Not Interested**: Pass
- **Bad Fit**: Wrong target

## Configuration Options

Edit `config.py` to customize:

### Scraping Settings
```python
REQUEST_DELAY = 2.0  # Seconds between requests
MAX_G2_PAGES = 10    # Number of G2 pages to scrape
USE_CLOUDSCRAPER = True  # Anti-bot bypassing
```

### Target Criteria
```python
TARGET_COMPANY_SIZES = ["Small Business", "Mid-Market", "Enterprise"]
TARGET_INDUSTRIES = ["Technology", "SaaS", "E-commerce", ...]
MIN_COMPANY_SIZE = 10  # Minimum employees
```

### Processing Limits
```python
DAILY_LIMIT = 100  # Max companies per run
ENABLE_ENRICHMENT = True  # Find websites/LinkedIn
ENABLE_DEDUPLICATION = True  # Skip duplicates
```

## Advanced Usage

### Custom Known Customers

Edit `known_customers.py` to add your own list:

```python
KNOWN_ZENDESK_CUSTOMERS = [
    "Your Company 1",
    "Your Company 2",
    # ... add more
]
```

### Multiple Google Sheets

Run with different configurations:

```bash
# Sales team sheet
python main.py --mode full  # uses config.py

# Marketing team sheet (create config_marketing.py)
# Then modify main.py to use it
```

## Project Structure

```
lead-generator/
   main.py                 # Main pipeline orchestrator
   verify_setup.py         # Setup verification
   sheets_crm.py           # Google Sheets integration
   scraper_g2.py           # G2 scraper
   scraper_zendesk.py      # Zendesk showcase scraper
   enrichment.py           # Company enrichment
   known_customers.py      # Known customer database
   config_template.py      # Configuration template
   config.py               # Your configuration (create this)
   requirements.txt        # Python dependencies
   credentials.json        # Google credentials (download this)
   README.md               # This file
   QUICKSTART.md           # Quick setup guide
   .gitignore              # Git ignore rules
   logs/                   # Log files (created automatically)
```

## Security Notes

- `credentials.json` contains sensitive data - never commit to git
- `config.py` may contain sensitive data - never commit to git
- Both files are in `.gitignore` by default
- Share Google Sheet only with your service account email

## Contributing

This is a personal lead generation tool. Feel free to:
- Customize for your needs
- Add new data sources
- Improve scraping logic
- Add new enrichment sources

## License

This project is for personal/commercial use.

## Support

For issues:
1. Run `python verify_setup.py` to diagnose
2. Check the Troubleshooting section above
3. Review log files in `logs/` directory

## Success Tips

1. **Run daily** for best results - more companies over time
2. **Check data quality** weekly - verify websites and enrich manually if needed
3. **Update status** as you do outreach - track your progress
4. **Export regularly** to backup your data
5. **Start small** - test with 50 companies before scaling
6. **Personalize outreach** - use the company data to customize messages
7. **Track metrics** - measure response rates and adjust

## What's Next?

After 30 days, you'll have 1,500-3,000 Zendesk-using companies in your database. That's enough to:
- Run targeted email campaigns
- Start LinkedIn outreach
- Build lookalike audiences
- Identify partnership opportunities
- Analyze market segments
- Find competitors' customers

**Happy lead hunting!**
