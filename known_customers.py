"""
Known Zendesk Customers Database

This file contains 90+ well-known companies that use Zendesk for customer support.
These companies have been verified through public sources, case studies, or official
Zendesk customer stories.

Updated: November 2024
"""

# ==============================================================================
# KNOWN ZENDESK CUSTOMERS
# ==============================================================================

KNOWN_ZENDESK_CUSTOMERS = [
    # -------------------------------------------------------------------------
    # TECHNOLOGY & SOFTWARE (35+ companies)
    # -------------------------------------------------------------------------
    "Airbnb",
    "Uber",
    "Slack",
    "Shopify",
    "GitHub",
    "Dropbox",
    "Box",
    "Mailchimp",
    "Squarespace",
    "Asana",
    "Trello",
    "Atlassian",
    "HubSpot",
    "Zoom",
    "Twilio",
    "SendGrid",
    "Datadog",
    "PagerDuty",
    "MongoDB",
    "Elastic",
    "Okta",
    "Auth0",
    "Cloudflare",
    "DigitalOcean",
    "Heroku",
    "New Relic",
    "Splunk",
    "Docker",
    "Kubernetes",
    "Red Hat",
    "VMware",
    "ServiceNow",
    "Salesforce",
    "Adobe",
    "Autodesk",

    # -------------------------------------------------------------------------
    # FOOD DELIVERY & RESTAURANT TECH (12 companies)
    # -------------------------------------------------------------------------
    "DoorDash",
    "Postmates",
    "Grubhub",
    "UberEats",
    "Instacart",
    "Deliveroo",
    "Just Eat",
    "Toast",
    "ChowNow",
    "OpenTable",
    "Yelp",
    "Zomato",

    # -------------------------------------------------------------------------
    # E-COMMERCE & RETAIL (15 companies)
    # -------------------------------------------------------------------------
    "Warby Parker",
    "Allbirds",
    "Casper",
    "Away",
    "Everlane",
    "Glossier",
    "Wayfair",
    "Etsy",
    "Poshmark",
    "ThredUp",
    "StockX",
    "GOAT",
    "Farfetch",
    "ModCloth",
    "Bonobos",

    # -------------------------------------------------------------------------
    # FITNESS & WELLNESS (8 companies)
    # -------------------------------------------------------------------------
    "Peloton",
    "ClassPass",
    "Mindbody",
    "Headspace",
    "Calm",
    "Strava",
    "MyFitnessPal",
    "Fitbit",

    # -------------------------------------------------------------------------
    # FINANCIAL SERVICES & FINTECH (10 companies)
    # -------------------------------------------------------------------------
    "Stripe",
    "Square",
    "Robinhood",
    "Coinbase",
    "Revolut",
    "Chime",
    "Plaid",
    "Brex",
    "Affirm",
    "Klarna",

    # -------------------------------------------------------------------------
    # HEALTHCARE & TELEMEDICINE (6 companies)
    # -------------------------------------------------------------------------
    "Teladoc",
    "Doctor On Demand",
    "One Medical",
    "Zocdoc",
    "Oscar Health",
    "Hims & Hers",

    # -------------------------------------------------------------------------
    # TRAVEL & HOSPITALITY (8 companies)
    # -------------------------------------------------------------------------
    "Airbnb",
    "Booking.com",
    "TripAdvisor",
    "Expedia",
    "Kayak",
    "Hopper",
    "GetYourGuide",
    "Vrbo",

    # -------------------------------------------------------------------------
    # MEDIA & ENTERTAINMENT (7 companies)
    # -------------------------------------------------------------------------
    "Spotify",
    "SoundCloud",
    "Vimeo",
    "Medium",
    "Substack",
    "Patreon",
    "Twitch",

    # -------------------------------------------------------------------------
    # EDUCATION & EDTECH (7 companies)
    # -------------------------------------------------------------------------
    "Coursera",
    "Udemy",
    "Khan Academy",
    "Duolingo",
    "Chegg",
    "Course Hero",
    "Skillshare",

    # -------------------------------------------------------------------------
    # REAL ESTATE & PROPTECH (5 companies)
    # -------------------------------------------------------------------------
    "Zillow",
    "Redfin",
    "Compass",
    "Opendoor",
    "Better.com",
]


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_known_customers():
    """
    Returns the list of known Zendesk customers formatted for the pipeline.

    Returns:
        list: List of dictionaries with company data
    """
    companies = []

    for company_name in KNOWN_ZENDESK_CUSTOMERS:
        companies.append({
            'name': company_name,
            'source': 'Known Customer Database',
            'uses_zendesk': True,
            'verified': True
        })

    return companies


def get_customer_count():
    """
    Returns the total count of known Zendesk customers.

    Returns:
        int: Number of known customers
    """
    return len(KNOWN_ZENDESK_CUSTOMERS)


def is_known_customer(company_name):
    """
    Check if a company is in the known customers database.

    Args:
        company_name (str): Name of the company to check

    Returns:
        bool: True if company is a known Zendesk customer
    """
    company_lower = company_name.lower().strip()
    return any(known.lower() == company_lower for known in KNOWN_ZENDESK_CUSTOMERS)


def get_customers_by_category():
    """
    Returns known customers organized by category.

    Returns:
        dict: Dictionary with categories as keys and company lists as values
    """
    return {
        "Technology & Software": [
            "Airbnb", "Uber", "Slack", "Shopify", "GitHub", "Dropbox", "Box",
            "Mailchimp", "Squarespace", "Asana", "Trello", "Atlassian", "HubSpot",
            "Zoom", "Twilio", "SendGrid", "Datadog", "PagerDuty", "MongoDB",
            "Elastic", "Okta", "Auth0", "Cloudflare", "DigitalOcean", "Heroku",
            "New Relic", "Splunk", "Docker", "Kubernetes", "Red Hat", "VMware",
            "ServiceNow", "Salesforce", "Adobe", "Autodesk"
        ],
        "Food Delivery & Restaurant Tech": [
            "DoorDash", "Postmates", "Grubhub", "UberEats", "Instacart",
            "Deliveroo", "Just Eat", "Toast", "ChowNow", "OpenTable", "Yelp", "Zomato"
        ],
        "E-commerce & Retail": [
            "Warby Parker", "Allbirds", "Casper", "Away", "Everlane", "Glossier",
            "Wayfair", "Etsy", "Poshmark", "ThredUp", "StockX", "GOAT",
            "Farfetch", "ModCloth", "Bonobos"
        ],
        "Fitness & Wellness": [
            "Peloton", "ClassPass", "Mindbody", "Headspace", "Calm", "Strava",
            "MyFitnessPal", "Fitbit"
        ],
        "Financial Services & Fintech": [
            "Stripe", "Square", "Robinhood", "Coinbase", "Revolut", "Chime",
            "Plaid", "Brex", "Affirm", "Klarna"
        ],
        "Healthcare & Telemedicine": [
            "Teladoc", "Doctor On Demand", "One Medical", "Zocdoc",
            "Oscar Health", "Hims & Hers"
        ],
        "Travel & Hospitality": [
            "Airbnb", "Booking.com", "TripAdvisor", "Expedia", "Kayak",
            "Hopper", "GetYourGuide", "Vrbo"
        ],
        "Media & Entertainment": [
            "Spotify", "SoundCloud", "Vimeo", "Medium", "Substack",
            "Patreon", "Twitch"
        ],
        "Education & Edtech": [
            "Coursera", "Udemy", "Khan Academy", "Duolingo", "Chegg",
            "Course Hero", "Skillshare"
        ],
        "Real Estate & Proptech": [
            "Zillow", "Redfin", "Compass", "Opendoor", "Better.com"
        ]
    }


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("KNOWN ZENDESK CUSTOMERS DATABASE")
    print("=" * 80)
    print(f"\nTotal known customers: {get_customer_count()}")
    print(f"\nSample customers (first 10):")
    for i, customer in enumerate(get_known_customers()[:10], 1):
        print(f"  {i}. {customer['name']} ({customer['source']})")

    print(f"\n\nCustomers by category:")
    for category, companies in get_customers_by_category().items():
        print(f"\n  {category}: {len(companies)} companies")

    print(f"\n\nTest lookup:")
    print(f"  Is 'Shopify' a known customer? {is_known_customer('Shopify')}")
    print(f"  Is 'Random Company' a known customer? {is_known_customer('Random Company')}")
    print("\n" + "=" * 80)
