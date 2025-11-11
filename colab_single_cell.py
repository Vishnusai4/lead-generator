"""
Zendesk Lead Generator - Single Cell Runner for Google Colab

Copy this entire cell into Google Colab and run it!
"""

# ============================================================================
# STEP 1: Clone Repository
# ============================================================================
print("📦 Cloning repository...")
!git clone https://github.com/Vishnusai4/lead-generator.git
%cd lead-generator
print("✅ Repository cloned\n")

# ============================================================================
# STEP 2: Install Dependencies
# ============================================================================
print("📦 Installing dependencies...")
!pip install -q requests beautifulsoup4 pyyaml cloudscraper fake-useragent playwright fastapi uvicorn python-dotenv
print("✅ Dependencies installed\n")

# ============================================================================
# STEP 3: Configure ScraperAPI
# ============================================================================
import os
SCRAPERAPI_KEY = "ee462d48408ee47a4258410b6da43640"
os.environ['SCRAPERAPI_KEY'] = SCRAPERAPI_KEY
print(f"✅ ScraperAPI configured: {SCRAPERAPI_KEY[:10]}...{SCRAPERAPI_KEY[-4:]}\n")

# ============================================================================
# STEP 4: Test Connectivity
# ============================================================================
print("🔍 Testing internet connectivity...\n")
import requests

tests = [
    ("Zendesk", "https://zendesk.com"),
    ("ScraperAPI", f"http://api.scraperapi.com/account?api_key={SCRAPERAPI_KEY}"),
    ("GitHub", "https://github.com")
]

for name, url in tests:
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print(f"✅ {name:20s} - OK (200)")
        elif r.status_code == 403:
            print(f"❌ {name:20s} - BLOCKED (403)")
        else:
            print(f"⚠️  {name:20s} - Status {r.status_code}")
    except Exception as e:
        print(f"❌ {name:20s} - Error: {str(e)[:50]}")

print("\n" + "="*80)

# ============================================================================
# STEP 5: Check Input File
# ============================================================================
print("\n📋 Checking input file...")
!ls -lh top_25k_us_focused_domains.csv
!echo "First 3 domains:"
!head -4 top_25k_us_focused_domains.csv

# ============================================================================
# STEP 6: Run Test (100 domains)
# ============================================================================
print("\n" + "="*80)
print("🚀 RUNNING TEST: 100 domains")
print("="*80 + "\n")

!head -101 top_25k_us_focused_domains.csv > test_100.csv
!python run_pipeline.py \
  --input test_100.csv \
  --output test_results.csv \
  --threads 10 \
  --us-only

# ============================================================================
# STEP 7: Show Test Results
# ============================================================================
print("\n" + "="*80)
print("📊 TEST RESULTS")
print("="*80 + "\n")

import pandas as pd
df = pd.read_csv('test_results.csv')

print(f"Total processed: {len(df)}")
print(f"Zendesk detected: {df['detected_zendesk'].sum()}")
print(f"Blocked by WAF: {df['blocked_by_waf'].sum()}")
print(f"Detection rate: {df['detected_zendesk'].sum() / len(df) * 100:.1f}%")

detected = df[df['detected_zendesk'] == True]
if len(detected) > 0:
    print(f"\n✅ Found {len(detected)} companies using Zendesk:\n")
    print(detected[['domain', 'company_name', 'zendesk_score']].head(10))
else:
    print("\n⚠️  No Zendesk detected in this sample (normal for top tech companies)")

print("\n" + "="*80)
print("✅ Test complete! Ready to run full 25K pipeline.")
print("="*80)
