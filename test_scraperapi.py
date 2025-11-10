#!/usr/bin/env python3
"""
Test ScraperAPI integration

Before running:
1. Sign up at https://www.scraperapi.com/ (FREE - 1,000 requests/month)
2. Get your API key from dashboard
3. Set environment variable: export SCRAPERAPI_KEY=your_key_here
4. Run: python test_scraperapi.py
"""

import os
import sys
from detect_zendesk import ZendeskDetector

# Check if API key is set
api_key = os.getenv('SCRAPERAPI_KEY')
if not api_key:
    print("❌ ERROR: SCRAPERAPI_KEY not set!")
    print("\n📝 Setup Instructions:")
    print("1. Sign up at https://www.scraperapi.com/")
    print("2. Get your FREE API key (1,000 requests/month)")
    print("3. Run: export SCRAPERAPI_KEY=your_key_here")
    print("4. Then run this script again")
    sys.exit(1)

print("=" * 80)
print("SCRAPERAPI INTEGRATION TEST")
print("=" * 80)

# Test domains that were previously blocked
test_domains = [
    "zendesk.com",      # Should be blocked without ScraperAPI
    "freshdesk.com",    # Support platform
    "shopify.com",      # E-commerce
]

print(f"\n✅ ScraperAPI key found: {api_key[:10]}...{api_key[-4:]}")
print(f"\n🧪 Testing {len(test_domains)} domains with ScraperAPI bypass...")
print("\n" + "-" * 80)

# Initialize detector WITH ScraperAPI
detector = ZendeskDetector(scraperapi_key=api_key)

for i, domain in enumerate(test_domains, 1):
    print(f"\n[{i}/{len(test_domains)}] Testing {domain}...")

    result = detector.detect(domain)

    detected = "✓ DETECTED" if result['detected'] else "✗ Not detected"
    blocked = "(BLOCKED)" if result.get('blocked_by_waf') else "(SUCCESS)"
    method = result.get('method', 'unknown')
    score = result.get('score', 0)

    print(f"  Result: {detected} {blocked}")
    print(f"  Method: {method}")
    print(f"  Score: {score}")
    print(f"  Signals: {len(result.get('signals', {}))}")

    if result.get('error'):
        print(f"  Error: {result['error']}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\n📊 ScraperAPI Usage:")
print(f"  • Requests used: {len(test_domains)}")
print(f"  • Check dashboard: https://www.scraperapi.com/dashboard")
print("\n💡 Tips:")
print("  • Free tier: 1,000 requests/month")
print("  • Each request = 1 credit")
print("  • JS rendering = 5 credits (not enabled by default)")
print("  • Paid plans start at $49/month")
