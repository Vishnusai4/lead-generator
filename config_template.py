"""
Configuration Template for Zendesk Lead Finder

INSTRUCTIONS:
1. Copy this file to config.py: cp config_template.py config.py
2. Fill in your Google Sheets credentials and sheet name
3. Adjust scraping and target settings as needed
4. Never commit config.py to git (it's in .gitignore)
"""

# ==============================================================================
# GOOGLE SHEETS CONFIGURATION
# ==============================================================================

# Path to your Google Service Account credentials JSON file
# Download this from Google Cloud Console > Service Accounts
GOOGLE_SHEETS_CREDENTIALS_PATH = "credentials.json"

# Name of your Google Sheet (will be created if it doesn't exist)
GOOGLE_SHEET_NAME = "Teravictus Leads"

# Name of the worksheet/tab within the Google Sheet
WORKSHEET_NAME = "Companies"


# ==============================================================================
# SCRAPING CONFIGURATION
# ==============================================================================

# User agent string to identify our scraper
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Delay between requests (seconds) - be respectful!
REQUEST_DELAY = 2.0

# Delay between enrichment requests (seconds)
ENRICHMENT_DELAY = 1.0

# Maximum number of pages to scrape from each source
MAX_G2_PAGES = 10

# Timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 30


# ==============================================================================
# SOURCE URLS
# ==============================================================================

# G2 reviews page for Zendesk
G2_ZENDESK_URL = "https://www.g2.com/products/zendesk/reviews"

# Zendesk customer showcase page
ZENDESK_CUSTOMERS_URL = "https://www.zendesk.com/customers/"

# Alternative Zendesk customer pages
ZENDESK_SHOWCASE_URLS = [
    "https://www.zendesk.com/customers/",
    "https://www.zendesk.com/customer-stories/",
]


# ==============================================================================
# TARGET CRITERIA
# ==============================================================================

# Company sizes to target (leave empty to target all)
TARGET_COMPANY_SIZES = [
    "Small Business",
    "Mid-Market",
    "Enterprise",
]

# Industries to prioritize (leave empty to target all)
TARGET_INDUSTRIES = [
    "Technology",
    "Software",
    "SaaS",
    "E-commerce",
    "Retail",
    "Healthcare",
    "Financial Services",
    "Education",
    "Media",
    "Travel",
]

# Minimum company size to consider (employees)
MIN_COMPANY_SIZE = 10

# Maximum company size to consider (employees, 0 = no limit)
MAX_COMPANY_SIZE = 0


# ==============================================================================
# PROCESSING LIMITS
# ==============================================================================

# Maximum number of companies to process per day
DAILY_LIMIT = 100

# Maximum number of companies to enrich per batch
ENRICHMENT_BATCH_SIZE = 10

# Enable/disable enrichment (finding websites and LinkedIn URLs)
ENABLE_ENRICHMENT = True

# Enable/disable duplicate checking
ENABLE_DEDUPLICATION = True


# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

# Enable verbose logging
VERBOSE_LOGGING = True

# Log file path (set to None to disable file logging)
LOG_FILE_PATH = "logs/lead_finder.log"

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"


# ==============================================================================
# ADVANCED SETTINGS
# ==============================================================================

# Retry failed requests (number of attempts)
MAX_RETRIES = 3

# Use cloudscraper for anti-bot bypassing
USE_CLOUDSCRAPER = True

# Selenium browser for JavaScript-heavy sites (chrome, firefox, safari)
SELENIUM_BROWSER = "chrome"

# Run Selenium in headless mode
SELENIUM_HEADLESS = True

# Enable known customers database
USE_KNOWN_CUSTOMERS = True
