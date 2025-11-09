#!/usr/bin/env python3
"""
Verify Zendesk Usage - Check if companies actually use Zendesk

This script helps verify which companies in your list actually use Zendesk
by checking their support/help pages for Zendesk indicators.

Usage:
    python verify_zendesk_usage.py
"""

import requests
import csv
from urllib.parse import urlparse
import time


def check_for_zendesk(company_name, timeout=10):
    """
    Check if a company uses Zendesk by examining their support page.

    Args:
        company_name (str): Name of the company
        timeout (int): Request timeout in seconds

    Returns:
        dict: Verification results
    """
    result = {
        'company': company_name,
        'likely_uses_zendesk': False,
        'confidence': 'Unknown',
        'evidence': [],
        'support_url': None
    }

    # Common support URL patterns
    support_urls = [
        f"https://support.{company_name.lower().replace(' ', '')}.com",
        f"https://help.{company_name.lower().replace(' ', '')}.com",
        f"https://{company_name.lower().replace(' ', '')}.zendesk.com",
    ]

    for url in support_urls:
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)

            if response.status_code == 200:
                content = response.text.lower()

                # Check for Zendesk indicators
                zendesk_indicators = [
                    'zendesk',
                    'powered by zendesk',
                    'zendesk.com',
                    'zdassets',
                    'zdcdn.net'
                ]

                found_indicators = [ind for ind in zendesk_indicators if ind in content]

                if found_indicators:
                    result['likely_uses_zendesk'] = True
                    result['support_url'] = url
                    result['evidence'] = found_indicators

                    # Determine confidence
                    if 'powered by zendesk' in content:
                        result['confidence'] = 'High'
                    elif len(found_indicators) >= 2:
                        result['confidence'] = 'Medium'
                    else:
                        result['confidence'] = 'Low'

                    return result

        except Exception as e:
            continue

    return result


def verify_companies_from_csv(csv_file='leads.csv', output_file='verified_leads.csv'):
    """
    Verify companies from CSV file.

    Args:
        csv_file (str): Input CSV file
        output_file (str): Output CSV file with verification results
    """
    verified_companies = []

    print("=" * 80)
    print("ZENDESK USAGE VERIFICATION")
    print("=" * 80)
    print(f"\nReading companies from: {csv_file}\n")

    # Read companies from CSV
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        companies = list(reader)

    total = len(companies)
    verified_count = 0

    for i, company_row in enumerate(companies, 1):
        company_name = company_row['Company Name']

        print(f"[{i}/{total}] Checking {company_name}...", end=" ")

        # Verify
        result = check_for_zendesk(company_name)

        # Update row with verification data
        company_row['Verified Uses Zendesk'] = 'Yes' if result['likely_uses_zendesk'] else 'Unverified'
        company_row['Verification Confidence'] = result['confidence']
        company_row['Support URL'] = result['support_url'] or ''
        company_row['Evidence'] = ', '.join(result['evidence']) if result['evidence'] else ''

        verified_companies.append(company_row)

        if result['likely_uses_zendesk']:
            verified_count += 1
            print(f"✓ VERIFIED ({result['confidence']} confidence)")
        else:
            print("✗ Could not verify")

        # Be respectful - add delay
        if i < total:
            time.sleep(2)

    # Write results
    fieldnames = list(companies[0].keys()) + ['Verified Uses Zendesk', 'Verification Confidence', 'Support URL', 'Evidence']

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(verified_companies)

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total companies checked: {total}")
    print(f"Verified using Zendesk: {verified_count}")
    print(f"Verification rate: {verified_count/total*100:.1f}%")
    print(f"\nResults saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will make HTTP requests to each company's website.")
    print("This may take several minutes (2-second delay between checks).\n")

    response = input("Continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        verify_companies_from_csv()
    else:
        print("Verification cancelled.")
