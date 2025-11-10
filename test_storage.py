#!/usr/bin/env python3
"""
Quick test of storage layer functionality.
"""

import os
from storage import LeadStorage
from datetime import datetime

def test_storage():
    print("=" * 80)
    print("TESTING STORAGE LAYER")
    print("=" * 80)

    # Clean up test files if they exist
    test_db = 'test_leads.db'
    test_csv = 'test_leads.csv'

    for f in [test_db, test_csv]:
        if os.path.exists(f):
            os.remove(f)

    # Initialize storage
    print("\n1. Initializing storage...")
    storage = LeadStorage(db_path=test_db, csv_path=test_csv)
    print("✓ Storage initialized")

    # Test saving a lead with detection data
    print("\n2. Saving test lead with Zendesk detection...")
    lead1 = {
        'company_name': 'Shopify',
        'domain': 'shopify.com',
        'detected_zendesk': True,
        'zendesk_score': 180,
        'signals': {
            'script_zendesk': True,
            'window_ze': True,
            'xhr_zendesk': True
        },
        'employees': 5000,
        'industry': 'E-commerce',
        'country': 'United States',
        'state': 'California',
        'city': 'San Francisco',
        'linkedin_url': 'https://linkedin.com/company/shopify',
        'enriched_at': datetime.utcnow().isoformat(),
        'detection_timestamp': datetime.utcnow().isoformat(),
        'blocked_by_waf': False,
        'original_status_code': 200,
        'original_headers': '{}',
        'detection_method': 'fast'
    }

    storage.save_lead(lead1)
    print("✓ Lead saved")

    # Test saving a blocked lead
    print("\n3. Saving test lead with WAF blocking...")
    lead2 = {
        'company_name': 'Stripe',
        'domain': 'stripe.com',
        'detected_zendesk': False,
        'zendesk_score': 0,
        'signals': {},
        'country': 'United States',
        'state': 'California',
        'city': 'San Francisco',
        'detection_timestamp': datetime.utcnow().isoformat(),
        'blocked_by_waf': True,
        'original_status_code': 403,
        'original_headers': '{"server": "cloudflare"}',
        'detection_method': 'fast_blocked'
    }

    storage.save_lead(lead2)
    print("✓ Blocked lead saved")

    # Test retrieval
    print("\n4. Retrieving lead...")
    retrieved = storage.get_lead('shopify.com')
    print(f"✓ Retrieved: {retrieved['company_name']}")
    print(f"  - Detected: {retrieved['detected_zendesk']}")
    print(f"  - Score: {retrieved['zendesk_score']}")
    print(f"  - Signals: {retrieved['signals']}")

    # Test stats
    print("\n5. Getting database stats...")
    stats = storage.get_stats()
    print(f"✓ Total leads: {stats['total_leads']}")
    print(f"  - Zendesk detected: {stats['zendesk_detected']}")
    print(f"  - Blocked by WAF: {stats['blocked_by_waf']}")
    print(f"  - US companies: {stats['us_companies']}")

    # Test CSV export
    print("\n6. Exporting to CSV...")
    storage.export_to_csv()
    print(f"✓ Exported to {test_csv}")

    # Test filtering
    print("\n7. Testing filtered queries...")
    detected = storage.get_all_leads(detected_only=True)
    print(f"✓ Detected only: {len(detected)} leads")

    blocked = storage.get_blocked_leads()
    print(f"✓ Blocked by WAF: {len(blocked)} leads")

    # Test update
    print("\n8. Testing update...")
    lead1['zendesk_score'] = 200
    storage.save_lead(lead1)
    updated = storage.get_lead('shopify.com')
    print(f"✓ Updated score: {updated['zendesk_score']}")

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED")
    print("=" * 80)

    # Clean up
    for f in [test_db, test_csv]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    test_storage()
