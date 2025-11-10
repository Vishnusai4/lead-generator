#!/usr/bin/env python3
"""
Simple Zendesk Verification Script

Reads domains from seed.csv, detects Zendesk usage, outputs verified list.
No complex infrastructure - just detection and CSV output.
"""

import csv
import time
from detect_zendesk import ZendeskDetector
from datetime import datetime


def verify_domains(input_csv='examples/seed.csv', output_csv='zendesk_verified.csv'):
    """
    Verify Zendesk usage for all domains in input CSV.

    Args:
        input_csv: Path to input CSV with 'domain' column
        output_csv: Path to output CSV with results
    """
    print("=" * 80)
    print("ZENDESK VERIFICATION")
    print("=" * 80)
    print(f"\nInput: {input_csv}")
    print(f"Output: {output_csv}\n")

    # Initialize detector
    detector = ZendeskDetector()

    # Read domains
    domains = []
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domains.append(row['domain'])

    print(f"Found {len(domains)} domains to check\n")

    # Verify each domain
    results = []
    verified_count = 0

    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{len(domains)}] Checking {domain}...", end=" ")

        try:
            result = detector.detect(domain)

            # Add to results
            results.append({
                'domain': domain,
                'uses_zendesk': 'Yes' if result['detected'] else 'No',
                'confidence_score': result['score'],
                'detection_method': result['method'],
                'signals_found': ', '.join(result['signals'].keys()),
                'checked_at': result['timestamp']
            })

            if result['detected']:
                verified_count += 1
                print(f"✓ VERIFIED (score: {result['score']})")
            else:
                print(f"✗ Not detected (score: {result['score']})")

        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append({
                'domain': domain,
                'uses_zendesk': 'Error',
                'confidence_score': 0,
                'detection_method': 'error',
                'signals_found': str(e),
                'checked_at': datetime.utcnow().isoformat()
            })

        # Rate limiting
        if i < len(domains):
            time.sleep(1)

    # Write results
    with open(output_csv, 'w', newline='') as f:
        fieldnames = ['domain', 'uses_zendesk', 'confidence_score', 'detection_method', 'signals_found', 'checked_at']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print(f"Total domains checked: {len(domains)}")
    print(f"✓ Verified using Zendesk: {verified_count}")
    print(f"✗ Not using Zendesk: {len(domains) - verified_count}")
    print(f"Verification rate: {verified_count/len(domains)*100:.1f}%")
    print(f"\nResults saved to: {output_csv}")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Verify Zendesk usage for domains')
    parser.add_argument('--input', default='examples/seed.csv', help='Input CSV file')
    parser.add_argument('--output', default='zendesk_verified.csv', help='Output CSV file')

    args = parser.parse_args()

    verify_domains(args.input, args.output)
