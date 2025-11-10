"""
Company Enrichment Module

Pluggable interface for enriching company data with business intelligence.
Supports multiple providers with automatic fallback.

Providers:
1. Clearbit (paid, high quality)
2. Free fallback (WHOIS + web scraping)
"""

import os
import re
import logging
import requests
from typing import Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import socket

logger = logging.getLogger(__name__)


class EnrichmentProvider:
    """Base class for enrichment providers."""

    def enrich(self, domain: str) -> Optional[Dict]:
        """
        Enrich company data for a domain.

        Args:
            domain: Company domain

        Returns:
            dict: Enriched data or None if failed
        """
        raise NotImplementedError


class ClearbitProvider(EnrichmentProvider):
    """
    Clearbit Company API enrichment.

    Requires CLEARBIT_API_KEY environment variable.
    """

    API_URL = "https://company.clearbit.com/v2/companies/find"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Clearbit provider.

        Args:
            api_key: Clearbit API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv('CLEARBIT_API_KEY')

        if not self.api_key:
            logger.warning("Clearbit API key not configured")

    def enrich(self, domain: str) -> Optional[Dict]:
        """Enrich using Clearbit API."""
        if not self.api_key:
            logger.debug(f"{domain}: Clearbit API key not available")
            return None

        try:
            response = requests.get(
                self.API_URL,
                params={'domain': domain},
                auth=(self.api_key, ''),
                timeout=10
            )

            if response.status_code == 404:
                logger.debug(f"{domain}: Not found in Clearbit")
                return None

            if response.status_code != 200:
                logger.warning(f"{domain}: Clearbit API error {response.status_code}")
                return None

            data = response.json()

            # Extract relevant fields
            enriched = {
                'company_name': data.get('name'),
                'employees': self._parse_employees(data.get('metrics', {}).get('employees')),
                'industry': data.get('category', {}).get('industry'),
                'country': data.get('geo', {}).get('country'),
                'state': data.get('geo', {}).get('state'),
                'city': data.get('geo', {}).get('city'),
                'linkedin_url': data.get('linkedin', {}).get('handle'),
                'description': data.get('description'),
                'enrichment_source': 'clearbit',
                'enriched_at': datetime.utcnow().isoformat()
            }

            # Convert LinkedIn handle to full URL
            if enriched['linkedin_url'] and not enriched['linkedin_url'].startswith('http'):
                enriched['linkedin_url'] = f"https://linkedin.com/company/{enriched['linkedin_url']}"

            logger.info(f"{domain}: Enriched via Clearbit")
            return enriched

        except requests.RequestException as e:
            logger.error(f"{domain}: Clearbit request failed - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"{domain}: Clearbit enrichment error - {str(e)}")
            return None

    def _parse_employees(self, employees_data) -> Optional[int]:
        """Parse employee count from various formats."""
        if isinstance(employees_data, int):
            return employees_data

        if isinstance(employees_data, str):
            # Extract number from ranges like "50-100"
            match = re.search(r'(\d+)', employees_data)
            if match:
                return int(match.group(1))

        return None


class FreeProvider(EnrichmentProvider):
    """
    Free enrichment using web scraping and WHOIS.

    Lower quality but no API key required.
    """

    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    def enrich(self, domain: str) -> Optional[Dict]:
        """Enrich using free sources."""
        try:
            enriched = {
                'company_name': self._extract_company_name(domain),
                'country': self._get_country_from_tld(domain),
                'enrichment_source': 'free_scraping',
                'enriched_at': datetime.utcnow().isoformat()
            }

            # Try to get additional info from homepage
            homepage_data = self._scrape_homepage(domain)
            if homepage_data:
                enriched.update(homepage_data)

            logger.info(f"{domain}: Enriched via free provider")
            return enriched

        except Exception as e:
            logger.error(f"{domain}: Free enrichment failed - {str(e)}")
            return None

    def _extract_company_name(self, domain: str) -> str:
        """Extract likely company name from domain."""
        # Remove TLD and common suffixes
        name = domain.split('.')[0]

        # Convert to title case and clean up
        name = name.replace('-', ' ').replace('_', ' ').title()

        return name

    def _get_country_from_tld(self, domain: str) -> Optional[str]:
        """Infer country from TLD."""
        tld_mapping = {
            '.us': 'United States',
            '.uk': 'United Kingdom',
            '.ca': 'Canada',
            '.de': 'Germany',
            '.fr': 'France',
            '.jp': 'Japan',
            '.cn': 'China',
            '.au': 'Australia',
            '.in': 'India',
            '.br': 'Brazil'
        }

        for tld, country in tld_mapping.items():
            if domain.endswith(tld):
                return country

        # Default assumption for .com domains
        if domain.endswith('.com'):
            return 'United States'

        return None

    def _scrape_homepage(self, domain: str) -> Optional[Dict]:
        """Try to extract company info from homepage."""
        try:
            url = f"https://{domain}"
            response = requests.get(
                url,
                headers={'User-Agent': self.user_agent},
                timeout=10,
                allow_redirects=True
            )

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            data = {}

            # Try to find company name in title or meta tags
            if soup.title:
                data['company_name'] = soup.title.string.strip()

            # Try to find description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                data['description'] = meta_desc['content']

            # Try to find LinkedIn link
            linkedin_link = soup.find('a', href=re.compile(r'linkedin\.com/company'))
            if linkedin_link:
                data['linkedin_url'] = linkedin_link['href']

            return data

        except Exception as e:
            logger.debug(f"{domain}: Homepage scraping failed - {str(e)}")
            return None


class CompanyEnricher:
    """
    Main enrichment coordinator with provider fallback.

    Features:
    - Tries Clearbit first (if configured)
    - Falls back to free scraping
    - US-only filtering
    - Caching support
    """

    def __init__(self, clearbit_api_key: Optional[str] = None,
                 us_only: bool = True):
        """
        Initialize enricher with providers.

        Args:
            clearbit_api_key: Optional Clearbit API key
            us_only: Only return US-based companies
        """
        self.us_only = us_only

        # Initialize providers
        self.providers = []

        # Add Clearbit if configured
        clearbit = ClearbitProvider(api_key=clearbit_api_key)
        if clearbit.api_key:
            self.providers.append(clearbit)
            logger.info("Clearbit provider enabled")
        else:
            logger.info("Clearbit provider disabled (no API key)")

        # Always add free provider as fallback
        self.providers.append(FreeProvider())
        logger.info("Free provider enabled")

    def enrich(self, domain: str) -> Optional[Dict]:
        """
        Enrich company data with provider fallback.

        Args:
            domain: Company domain

        Returns:
            dict: Enriched data or None if all providers failed
        """
        logger.info(f"Enriching {domain}...")

        # Try each provider in order
        for provider in self.providers:
            provider_name = provider.__class__.__name__
            logger.debug(f"{domain}: Trying {provider_name}")

            enriched = provider.enrich(domain)

            if enriched:
                # Apply US-only filter
                if self.us_only:
                    country = enriched.get('country')

                    if country and country != 'United States':
                        logger.info(f"{domain}: Filtered out (country: {country})")
                        return None

                logger.info(f"{domain}: Successfully enriched via {provider_name}")
                return enriched

        logger.warning(f"{domain}: All enrichment providers failed")
        return None

    def enrich_batch(self, domains: list) -> Dict[str, Optional[Dict]]:
        """
        Enrich multiple domains.

        Args:
            domains: List of domains to enrich

        Returns:
            dict: Mapping of domain -> enriched data
        """
        results = {}

        for domain in domains:
            results[domain] = self.enrich(domain)

        return results

    def is_us_company(self, enriched_data: Dict) -> bool:
        """Check if enriched data indicates US company."""
        country = enriched_data.get('country')
        return country == 'United States'

    def get_stats(self, enriched_results: Dict[str, Optional[Dict]]) -> Dict:
        """
        Get statistics about enrichment batch.

        Args:
            enriched_results: Results from enrich_batch()

        Returns:
            dict: Statistics
        """
        total = len(enriched_results)
        successful = sum(1 for v in enriched_results.values() if v is not None)
        us_companies = sum(
            1 for v in enriched_results.values()
            if v and v.get('country') == 'United States'
        )

        sources = {}
        for data in enriched_results.values():
            if data:
                source = data.get('enrichment_source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

        return {
            'total': total,
            'successful': successful,
            'failed': total - successful,
            'us_companies': us_companies,
            'success_rate': successful / total if total > 0 else 0,
            'sources': sources
        }


# Convenience functions for direct usage

def enrich_domain(domain: str, clearbit_api_key: Optional[str] = None,
                  us_only: bool = True) -> Optional[Dict]:
    """
    Enrich a single domain.

    Args:
        domain: Company domain
        clearbit_api_key: Optional Clearbit API key
        us_only: Only return US companies

    Returns:
        dict: Enriched data or None
    """
    enricher = CompanyEnricher(clearbit_api_key=clearbit_api_key, us_only=us_only)
    return enricher.enrich(domain)


def enrich_domains(domains: list, clearbit_api_key: Optional[str] = None,
                   us_only: bool = True) -> Dict[str, Optional[Dict]]:
    """
    Enrich multiple domains.

    Args:
        domains: List of domains
        clearbit_api_key: Optional Clearbit API key
        us_only: Only return US companies

    Returns:
        dict: Mapping of domain -> enriched data
    """
    enricher = CompanyEnricher(clearbit_api_key=clearbit_api_key, us_only=us_only)
    return enricher.enrich_batch(domains)
