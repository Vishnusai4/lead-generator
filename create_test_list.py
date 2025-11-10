#!/usr/bin/env python3
"""
Create a comprehensive test domain list from known sources
"""

# Top SaaS companies
saas_companies = [
    "salesforce.com", "servicenow.com", "workday.com", "oracle.com", "sap.com",
    "adobe.com", "microsoft.com", "google.com", "amazon.com", "zoom.us",
    "slack.com", "atlassian.com", "hubspot.com", "zendesk.com", "intercom.com",
    "freshworks.com", "zoho.com", "monday.com", "asana.com", "notion.so",
    "airtable.com", "clickup.com", "miro.com", "figma.com", "canva.com",
    "dropbox.com", "box.com", "docusign.com", "twilio.com", "stripe.com",
    "shopify.com", "squarespace.com", "wix.com", "wordpress.com", "mailchimp.com",
    "sendgrid.com", "constant-contact.com", "activecampaign.com", "klaviyo.com",
    "segment.com", "amplitude.com", "mixpanel.com", "heap.io", "fullstory.com",
    "hotjar.com", "optimizely.com", "unbounce.com", "instapage.com", "leadpages.com"
]

# E-commerce platforms
ecommerce = [
    "bigcommerce.com", "magento.com", "woocommerce.com", "prestashop.com",
    "3dcart.com", "volusion.com", "ecwid.com", "bigcartel.com", "shift4shop.com",
    "commercetools.com", "elastic.co", "algolia.com", "searchspring.com"
]

# Customer support / CRM
support_crm = [
    "salesforce.com", "hubspot.com", "pipedrive.com", "zoho.com", "freshsales.com",
    "nutshell.com", "insightly.com", "copper.com", "nimble.com", "keap.com",
    "gorgias.com", "kustomer.com", "helpscout.com", "groove.com", "drift.com",
    "livechat.com", "tawk.to", "olark.com", "pure.chat", "userlike.com",
    "crisp.chat", "chatwoot.com", "tidio.com", "smartsupp.com", "chatra.com"
]

# HR / Recruiting
hr_recruiting = [
    "greenhouse.io", "lever.co", "workable.com", "bamboohr.com", "namely.com",
    "gusto.com", "rippling.com", "justworks.com", "zenefits.com", "adp.com",
    "paychex.com", "paylocity.com", "ultipro.com", "ceridian.com", "namely.com"
]

# Marketing automation
marketing = [
    "marketo.com", "pardot.com", "eloqua.com", "activecampaign.com",
    "getresponse.com", "convertkit.com", "drip.com", "sendinblue.com",
    "mailerlite.com", "moosend.com", "benchmark.com", "campaignmonitor.com",
    "aweber.com", "madmimi.com", "vertical-response.com"
]

# Project management
project_mgmt = [
    "trello.com", "basecamp.com", "teamwork.com", "wrike.com", "smartsheet.com",
    "clarizen.com", "liquid-planner.com", "mavenlink.com", "workfront.com",
    "projectmanager.com", "celoxis.com", "podio.com", "teamgantt.com"
]

# Communication / Collaboration
communication = [
    "teams.microsoft.com", "webex.com", "gotomeeting.com", "bluejeans.com",
    "whereby.com", "8x8.com", "ringcentral.com", "vonage.com", "dialpad.com",
    "grasshopper.com", "nextiva.com", "ooma.com", "jive.com", "mitel.com"
]

# Combine all
all_domains = list(set(
    saas_companies + ecommerce + support_crm +
    hr_recruiting + marketing + project_mgmt + communication
))

# Write to CSV
with open('large_test_domains.csv', 'w') as f:
    f.write('domain\\n')
    for domain in sorted(all_domains):
        f.write(f'{domain}\\n')

print(f"Created large_test_domains.csv with {len(all_domains)} domains")
print(f"Categories: SaaS, E-commerce, Support/CRM, HR, Marketing, PM, Communication")
