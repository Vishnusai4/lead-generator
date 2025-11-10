#!/usr/bin/env python3
"""
Generate large domain list from common patterns and known sources
"""

# Common SaaS/business domain patterns
common_names = [
    # Software/SaaS
    "app", "cloud", "suite", "soft", "tech", "sys", "data", "intel", "smart", "pro",
    "solutions", "systems", "software", "platform", "hub", "central", "base", "core",
    "team", "work", "desk", "space", "flow", "sync", "connect", "link", "bridge",

    # Business types
    "crm", "erp", "hrm", "cms", "lms", "pos", "ecommerce", "shop", "store", "market",
    "pay", "finance", "accounting", "invoice", "bill", "expense", "time", "schedule",
    "project", "task", "plan", "track", "monitor", "analyze", "report", "insight",

    # Service types
    "support", "help", "service", "assist", "chat", "talk", "meet", "zoom", "call",
    "mail", "send", "message", "notify", "alert", "remind", "calendar", "book",
    "sign", "doc", "file", "drive", "share", "collaborate", "team", "group",

    # Industry specific
    "retail", "wholesale", "logistics", "shipping", "delivery", "transport",
    "hotel", "booking", "reservation", "travel", "tour", "trip",
    "health", "medical", "clinic", "care", "patient", "wellness",
    "edu", "learn", "teach", "train", "course", "academy", "school",
    "real-estate", "property", "listing", "agent", "broker",
    "legal", "law", "attorney", "court", "compliance",
    "insurance", "policy", "claim", "coverage",
    "bank", "credit", "loan", "mortgage", "invest"
]

prefixes = ["my", "get", "use", "go", "try", "the", "one", "all", "top", "best",
            "easy", "fast", "quick", "smart", "pro", "super", "ultra", "mega"]

suffixes = ["io", "app", "hq", "hub", "ly", "ai", "tech", "pro", "plus", "labs",
            "cloud", "works", "ware", "soft", "sys", "now", "live", "online"]

# Generate combinations
domains = []

# Pattern 1: name.com
for name in common_names[:100]:
    domains.append(f"{name}.com")

# Pattern 2: prefix-name.com
for prefix in prefixes[:20]:
    for name in common_names[:30]:
        domains.append(f"{prefix}{name}.com")
        domains.append(f"{prefix}-{name}.com")

# Pattern 3: name-suffix.com
for name in common_names[:50]:
    for suffix in suffixes[:15]:
        domains.append(f"{name}{suffix}.com")
        domains.append(f"{name}.{suffix}")

# Add known major companies by industry
major_companies = {
    "saas": ["salesforce.com", "servicenow.com", "workday.com", "oracle.com",
             "sap.com", "adobe.com", "microsoft.com", "atlassian.com"],
    "ecommerce": ["amazon.com", "shopify.com", "bigcommerce.com", "woocommerce.com",
                  "magento.com", "squarespace.com", "wix.com"],
    "fintech": ["stripe.com", "paypal.com", "square.com", "adyen.com", "braintree.com"],
    "crm": ["hubspot.com", "salesforce.com", "zoho.com", "pipedrive.com"],
    "support": ["zendesk.com", "intercom.com", "freshdesk.com", "helpscout.com"],
    "communication": ["slack.com", "zoom.us", "teams.microsoft.com", "webex.com"],
    "hr": ["workday.com", "bamboohr.com", "namely.com", "gusto.com", "adp.com"],
    "marketing": ["hubspot.com", "marketo.com", "mailchimp.com", "sendgrid.com"],
    "analytics": ["google.com", "amplitude.com", "mixpanel.com", "segment.com"],
    "productivity": ["asana.com", "monday.com", "trello.com", "notion.so", "airtable.com"]
}

for category, companies in major_companies.items():
    domains.extend(companies)

# Remove duplicates and sort
domains = sorted(list(set(domains)))

# Write to CSV
output_file = "synthetic_50k_domains.csv"
with open(output_file, 'w') as f:
    f.write('domain\n')
    for domain in domains[:50000]:  # Limit to 50k
        f.write(f'{domain}\n')

print(f"Created {output_file} with {min(len(domains), 50000)} domains")
print(f"Total unique combinations: {len(domains)}")
print(f"\nSample domains:")
for i, domain in enumerate(domains[:20]):
    print(f"  {i+1}. {domain}")
