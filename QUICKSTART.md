# Zendesk Lead Finder - Quick Start Guide

**Get up and running in 15 minutes!**

## Prerequisites

- Python 3.8+ installed
- Google account
- 15 minutes of your time

## Step-by-Step Setup

### 1. Install Dependencies (2 minutes)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Google Cloud Setup (5 minutes)

**A. Create Project & Enable APIs**

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project (any name)
3. Click "Enable APIs and Services"
4. Search and enable:
   - Google Sheets API
   - Google Drive API

**B. Create Service Account**

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name: `zendesk-lead-finder`
4. Click "Create and Continue" > "Continue" > "Done"

**C. Download Credentials**

1. Click on your new service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key" > "JSON"
4. Save file as `credentials.json` in project folder

**IMPORTANT:** Open `credentials.json` and copy the `client_email` value. You'll need it next!

Example: `zendesk-lead-finder@your-project.iam.gserviceaccount.com`

### 3. Google Sheets Setup (2 minutes)

1. Go to [sheets.google.com](https://sheets.google.com/)
2. Create a new spreadsheet
3. Name it: `Teravictus Leads`
4. Click "Share"
5. Paste the service account email (from credentials.json)
6. Change permission to "Editor"
7. Click "Send"

### 4. Configure (2 minutes)

```bash
# Copy configuration template
cp config_template.py config.py

# Edit with your favorite editor
nano config.py
```

Update these three lines:

```python
GOOGLE_SHEETS_CREDENTIALS_PATH = "credentials.json"
GOOGLE_SHEET_NAME = "Teravictus Leads"
WORKSHEET_NAME = "Companies"
```

Save and close.

### 5. Verify Setup (1 minute)

```bash
python verify_setup.py
```

**All checks must pass!** If any fail, follow the error messages to fix.

### 6. Test Run (2 minutes)

```bash
python main.py --mode test
```

This will:
- Test all scrapers
- Show you sample data
- NOT save to sheets (it's just a test!)

If you see sample companies, you're good!

### 7. First Full Run (3 minutes)

```bash
python main.py --mode full
```

This will:
- Scrape G2 and Zendesk
- Load 113 known customers
- Enrich with websites/LinkedIn
- Save to Google Sheets

**Expected:** 50-150 companies in your sheet!

### 8. View Results

Open your Google Sheet:
- `Teravictus Leads` spreadsheet
- `Companies` worksheet
- You should see companies with data!

---

## Daily Automation (Optional)

### Mac/Linux

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /path/to/lead-generator && /path/to/venv/bin/python main.py --mode full >> logs/cron.log 2>&1
```

### Windows

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Zendesk Lead Finder"
4. Trigger: Daily, 9:00 AM
5. Action: Start program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py --mode full`
   - Start in: `C:\path\to\lead-generator`

---

## Common Commands

```bash
# Full run (use this daily)
python main.py --mode full

# Test mode (verify everything works)
python main.py --mode test

# G2 only (faster)
python main.py --mode g2-only

# Zendesk only
python main.py --mode zendesk-only

# Skip enrichment (faster but less data)
python main.py --mode full --no-enrich

# Verify setup
python verify_setup.py
```

---

## Troubleshooting

### "config.py not found"
```bash
cp config_template.py config.py
# Then edit config.py
```

### "credentials.json not found"
- Download from Google Cloud Console (Step 2C)
- Place in project root folder
- Update path in config.py

### "Permission denied on Google Sheets"
- Share sheet with service account email
- Give "Editor" permission
- Service account email is in credentials.json

### "No companies found"
- Check internet connection
- Try: `python main.py --mode test`
- Known customers will always work (113 companies)

### Still stuck?
Run verification:
```bash
python verify_setup.py
```

---

## What You Get

### First Run
- 50-150 companies
- Company names, websites, LinkedIn URLs
- Industry and size data
- Ready for outreach!

### After 30 Days (Running Daily)
- 1,500-3,000 companies
- Extensive database
- No duplicates
- Enriched data

---

## Next Steps

**Week 1-2: Build Database**
- Run daily
- Let it collect companies
- Goal: 500+ companies

**Week 3-4: Find Contacts**
- Use Apollo.io or Hunter.io
- Find VP of Customer Success
- Add emails to spreadsheet

**Week 5+: Start Outreach**
- Email campaigns
- LinkedIn outreach
- Track results in "Status" column

---

## Pro Tips

1. Run it daily - consistency is key
2. Start reaching out after 100 companies
3. Update the "Status" column as you work
4. Export to CSV weekly as backup
5. Add custom notes in the "Notes" column
6. Filter by industry for targeted campaigns

---

## Success Metrics

After 30 days you should have:
- 1,500-3,000 companies in database
- 70%+ with websites
- 100% with LinkedIn URLs
- Ready to generate meetings/sales

---

## Need Help?

1. Check `README.md` for detailed docs
2. Run `python verify_setup.py`
3. Check logs in `logs/` directory

---

**You're all set! Start building your lead database today.**

Run this daily and watch your database grow:
```bash
python main.py --mode full
```

Good luck!
