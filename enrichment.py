"""
Company Enrichment Module

This module enriches company data with additional information like websites and LinkedIn URLs.
Uses free APIs and search engines to find company information.

Requirements:
- requests library
"""

import time
import re
import requests
from urllib.parse import quote, urlparse


class CompanyEnricher:
    """
    Enriches company data with websites, LinkedIn URLs, and additional information.
    Uses free APIs and public data sources.
    """

    def __init__(self, enrichment_delay=1.0):
        """
        Initialize the company enricher.

        Args:
            enrichment_delay (float): Delay between enrichment requests in seconds
        """
        self.enrichment_delay = enrichment_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def enrich_company(self, company_data):
        """
        Enrich a single company with additional data.

        Args:
            company_data (dict): Dictionary containing company information

        Returns:
            dict: Enhanced company data
        """
        company_name = company_data.get('name', '')

        if not company_name:
            return company_data

        print(f"\nEnriching: {company_name}")

        # Find website if not already present
        if not company_data.get('website'):
            website = self._find_website(company_name)
            if website:
                company_data['website'] = website
                print(f"  Found website: {website}")
            else:
                print(f"  Website not found")

        # Generate LinkedIn URL
        if not company_data.get('linkedin_url'):
            linkedin_url = self._find_linkedin(company_name)
            if linkedin_url:
                company_data['linkedin_url'] = linkedin_url
                print(f"  Generated LinkedIn: {linkedin_url}")

        # Validate website if found
        if company_data.get('website'):
            if self._validate_website(company_data['website']):
                print(f"  Website validated")
            else:
                print(f"  Website validation failed")

        return company_data

    def enrich_batch(self, companies_list):
        """
        Enrich multiple companies in batch.

        Args:
            companies_list (list): List of company dictionaries

        Returns:
            list: List of enriched company dictionaries
        """
        enriched_companies = []
        total = len(companies_list)

        print(f"\n{'='*60}")
        print(f"Starting enrichment: {total} companies")
        print(f"{'='*60}")

        for i, company in enumerate(companies_list, 1):
            print(f"\n[{i}/{total}]", end=" ")

            # Enrich company
            enriched = self.enrich_company(company)
            enriched_companies.append(enriched)

            # Delay before next enrichment (except on last one)
            if i < total and self.enrichment_delay > 0:
                time.sleep(self.enrichment_delay)

        print(f"\n{'='*60}")
        print(f"Enrichment complete!")
        print(f"{'='*60}\n")

        return enriched_companies

    def _find_website(self, company_name):
        """
        Find company website using DuckDuckGo instant answer API.

        Args:
            company_name (str): Name of the company

        Returns:
            str: Company website URL or empty string if not found
        """
        try:
            # Try DuckDuckGo Instant Answer API
            ddg_url = f"https://api.duckduckgo.com/?q={quote(company_name)}&format=json&no_html=1"

            response = self.session.get(ddg_url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Check for website in AbstractURL
                if data.get('AbstractURL'):
                    url = data['AbstractURL']
                    if self._is_valid_url(url):
                        return self._clean_url(url)

                # Check in RelatedTopics
                if data.get('RelatedTopics'):
                    for topic in data['RelatedTopics']:
                        if isinstance(topic, dict) and topic.get('FirstURL'):
                            url = topic['FirstURL']
                            if self._is_valid_url(url) and not 'duckduckgo.com' in url.lower():
                                return self._clean_url(url)

            # Fallback: Try to guess common domain patterns
            return self._guess_website(company_name)

        except Exception as e:
            print(f"  Error finding website: {str(e)}")
            return ""

    def _guess_website(self, company_name):
        """
        Guess company website based on common patterns.

        Args:
            company_name (str): Name of the company

        Returns:
            str: Guessed website URL or empty string
        """
        # Clean company name
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        clean_name = clean_name.strip()

        # Remove common suffixes
        suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited',
            'llc', 'company', 'co', 'technologies', 'tech', 'software',
            'solutions', 'services', 'systems', 'group'
        ]

        words = clean_name.split()
        filtered_words = [w for w in words if w not in suffixes]

        if not filtered_words:
            filtered_words = words

        # Try common patterns
        domain_base = ''.join(filtered_words)

        # Common domain patterns
        patterns = [
            f"https://{domain_base}.com",
            f"https://{''.join(words[:2])}.com" if len(words) >= 2 else None,
            f"https://{words[0]}.com" if words else None,
        ]

        # Return first valid pattern
        for pattern in patterns:
            if pattern:
                return pattern

        return ""

    def _find_linkedin(self, company_name):
        """
        Generate LinkedIn company page URL.

        Args:
            company_name (str): Name of the company

        Returns:
            str: LinkedIn company URL
        """
        # Clean company name for LinkedIn URL
        clean_name = re.sub(r'[^a-zA-Z0-9\s-]', '', company_name.lower())
        clean_name = clean_name.strip()

        # Replace spaces with hyphens
        linkedin_slug = clean_name.replace(' ', '-')

        # Remove multiple consecutive hyphens
        linkedin_slug = re.sub(r'-+', '-', linkedin_slug)

        # Generate LinkedIn URL
        linkedin_url = f"https://www.linkedin.com/company/{linkedin_slug}"

        return linkedin_url

    def _validate_website(self, url):
        """
        Validate that a website URL is accessible.

        Args:
            url (str): Website URL to validate

        Returns:
            bool: True if website is accessible
        """
        try:
            # Try to access the website
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code < 400

        except Exception:
            # If HEAD fails, try GET
            try:
                response = self.session.get(url, timeout=5, allow_redirects=True)
                return response.status_code < 400
            except Exception:
                return False

    def _is_valid_url(self, url):
        """
        Check if a URL is valid and not a common false positive.

        Args:
            url (str): URL to validate

        Returns:
            bool: True if valid URL
        """
        if not url:
            return False

        try:
            result = urlparse(url)
            # Must have scheme and netloc
            if not result.scheme or not result.netloc:
                return False

            # Filter out unwanted domains
            unwanted = [
                'wikipedia', 'facebook', 'twitter', 'linkedin',
                'instagram', 'youtube', 'duckduckgo', 'google'
            ]

            netloc_lower = result.netloc.lower()
            for unwanted_domain in unwanted:
                if unwanted_domain in netloc_lower:
                    return False

            return True

        except Exception:
            return False

    def _clean_url(self, url):
        """
        Clean and standardize a URL.

        Args:
            url (str): URL to clean

        Returns:
            str: Cleaned URL
        """
        if not url:
            return ""

        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Parse and reconstruct
        try:
            parsed = urlparse(url)
            # Reconstruct with just scheme, netloc, and path
            clean_url = f"{parsed.scheme}://{parsed.netloc}"
            if parsed.path and parsed.path != '/':
                clean_url += parsed.path

            return clean_url

        except Exception:
            return url

    def _extract_domain(self, url):
        """
        Extract domain from URL.

        Args:
            url (str): URL to extract domain from

        Returns:
            str: Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc

        except Exception:
            return ""

    def get_enrichment_stats(self, companies_list):
        """
        Get statistics about enrichment coverage.

        Args:
            companies_list (list): List of company dictionaries

        Returns:
            dict: Statistics about enrichment
        """
        stats = {
            'total': len(companies_list),
            'with_website': 0,
            'with_linkedin': 0,
            'with_both': 0,
            'with_neither': 0
        }

        for company in companies_list:
            has_website = bool(company.get('website'))
            has_linkedin = bool(company.get('linkedin_url'))

            if has_website:
                stats['with_website'] += 1
            if has_linkedin:
                stats['with_linkedin'] += 1
            if has_website and has_linkedin:
                stats['with_both'] += 1
            if not has_website and not has_linkedin:
                stats['with_neither'] += 1

        return stats


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("COMPANY ENRICHMENT TEST")
    print("=" * 80)

    # Test data
    test_companies = [
        {'name': 'Shopify', 'source': 'Test'},
        {'name': 'Slack', 'source': 'Test'},
        {'name': 'Airbnb', 'source': 'Test'},
    ]

    try:
        # Initialize enricher
        enricher = CompanyEnricher(enrichment_delay=1.0)

        # Test enrichment
        print("\nTesting company enrichment...")
        enriched = enricher.enrich_batch(test_companies)

        # Show results
        print("\n" + "=" * 80)
        print("ENRICHMENT RESULTS")
        print("=" * 80)

        for company in enriched:
            print(f"\nCompany: {company['name']}")
            print(f"  Website: {company.get('website', 'Not found')}")
            print(f"  LinkedIn: {company.get('linkedin_url', 'Not found')}")

        # Show stats
        stats = enricher.get_enrichment_stats(enriched)
        print("\n" + "=" * 80)
        print("ENRICHMENT STATISTICS")
        print("=" * 80)
        print(f"Total companies: {stats['total']}")
        print(f"With website: {stats['with_website']}")
        print(f"With LinkedIn: {stats['with_linkedin']}")
        print(f"With both: {stats['with_both']}")
        print(f"With neither: {stats['with_neither']}")

    except Exception as e:
        print(f"\nERROR during test: {str(e)}")

    print("\n" + "=" * 80)
