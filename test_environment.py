#!/usr/bin/env python3
"""
Test if your environment can run the Zendesk detector
Run this before starting the full pipeline to verify everything works
"""

import os
import sys

print("=" * 80)
print("ENVIRONMENT TEST FOR ZENDESK LEAD GENERATOR")
print("=" * 80)

# Test 1: Check Python version
print("\n1. Python Version Check")
if sys.version_info >= (3, 8):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.8+)")
    sys.exit(1)

# Test 2: Check dependencies
print("\n2. Dependency Check")
missing = []
try:
    import requests
    print("   ✅ requests")
except ImportError:
    missing.append("requests")
    print("   ❌ requests")

try:
    import bs4
    print("   ✅ beautifulsoup4")
except ImportError:
    missing.append("beautifulsoup4")
    print("   ❌ beautifulsoup4")

try:
    import cloudscraper
    print("   ✅ cloudscraper")
except ImportError:
    missing.append("cloudscraper")
    print("   ❌ cloudscraper")

if missing:
    print(f"\n   Missing: {', '.join(missing)}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Check internet connectivity
print("\n3. Internet Connectivity Check")
try:
    import requests
    r = requests.get("https://httpbin.org/get", timeout=10)
    if r.status_code == 200:
        print("   ✅ Can reach external websites")
    else:
        print(f"   ⚠️  Got status {r.status_code} (expected 200)")
except requests.exceptions.ProxyError:
    print("   ❌ Proxy blocking external access")
    print("   → You're in a sandboxed environment")
    print("   → Run this on your local machine or cloud instance")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Network error: {e}")
    sys.exit(1)

# Test 4: Check ScraperAPI (optional)
print("\n4. ScraperAPI Check (Optional)")
api_key = os.getenv('SCRAPERAPI_KEY')
if not api_key:
    print("   ⚠️  SCRAPERAPI_KEY not set (optional, but recommended)")
    print("   → Sign up at https://www.scraperapi.com/")
    print("   → Get 1,000 free requests/month")
    print("   → Set: export SCRAPERAPI_KEY=your_key")
else:
    print(f"   ✅ SCRAPERAPI_KEY found: {api_key[:10]}...{api_key[-4:]}")

    # Test API key validity
    try:
        import requests
        r = requests.get(
            "http://api.scraperapi.com/account",
            params={"api_key": api_key},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ API key valid")
            print(f"      Requests used: {data.get('requestCount', 'unknown')}")
            print(f"      Requests limit: {data.get('requestLimit', 'unknown')}")
        else:
            print(f"   ❌ API returned status {r.status_code}")
            if r.status_code == 403:
                print("   → Network is blocking ScraperAPI")
                print("   → Try from different network or use --use-cloudscraper")
    except Exception as e:
        print(f"   ❌ ScraperAPI test failed: {e}")

# Test 5: Test actual Zendesk detection
print("\n5. Zendesk Detection Test")
try:
    from detect_zendesk import ZendeskDetector

    # Test with a known Zendesk user
    detector = ZendeskDetector(scraperapi_key=api_key if api_key else None)
    result = detector.detect("zendesk.com")

    if result.get('blocked_by_waf'):
        print("   ⚠️  Test domain blocked by anti-bot")
        print("   → This is normal for high-security sites")
        print("   → ScraperAPI will help bypass this")
    elif result['detected']:
        print("   ✅ Detection working! Found Zendesk on zendesk.com")
    else:
        print("   ⚠️  Detection ran but didn't find Zendesk (unexpected)")

    print(f"      Method: {result.get('method', 'unknown')}")
    print(f"      Score: {result.get('score', 0)}")

except Exception as e:
    print(f"   ❌ Detection test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Check input file
print("\n6. Input File Check")
if os.path.exists("top_25k_us_focused_domains.csv"):
    with open("top_25k_us_focused_domains.csv") as f:
        lines = f.readlines()
        if lines[0].strip().lower() == "domain":
            print(f"   ✅ Found {len(lines)-1} domains in top_25k_us_focused_domains.csv")
        else:
            print(f"   ⚠️  CSV header should be 'domain' (found '{lines[0].strip()}')")
else:
    print("   ⚠️  top_25k_us_focused_domains.csv not found")
    print("   → Upload your domain list or use a different file")

# Summary
print("\n" + "=" * 80)
print("ENVIRONMENT TEST COMPLETE")
print("=" * 80)

if api_key:
    print("\n✅ You're ready to run the full pipeline!")
    print("\nRecommended command:")
    print("  python run_pipeline.py \\")
    print("    --input top_25k_us_focused_domains.csv \\")
    print("    --output zendesk_leads.csv \\")
    print("    --threads 10 \\")
    print("    --us-only")
else:
    print("\n⚠️  Ready to run, but ScraperAPI recommended for better results")
    print("\nWithout ScraperAPI:")
    print("  python run_pipeline.py \\")
    print("    --input top_25k_us_focused_domains.csv \\")
    print("    --output zendesk_leads.csv \\")
    print("    --use-cloudscraper \\")
    print("    --threads 5")

    print("\nWith ScraperAPI (recommended):")
    print("  1. Sign up: https://www.scraperapi.com/")
    print("  2. Get your free API key")
    print("  3. export SCRAPERAPI_KEY=your_key")
    print("  4. Run the command above (without --use-cloudscraper)")

print("\n💡 See RUN_LOCALLY.md for detailed instructions")
