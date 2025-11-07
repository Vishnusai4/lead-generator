"""
Zendesk Customer Showcase Scraper

This module scrapes Zendesk's official customer showcase and customer stories pages
to identify companies using Zendesk.

Requirements:
- requests or cloudscraper library
- beautifulsoup4 library
- fake-useragent library
"""

import time
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

try:
    import cloudscraper
    USE_CLOUDSCRAPER = True
except ImportError:
    import requests
    USE_CLOUDSCRAPER = False


class ZendeskShowcaseScraper:
    """
    Scraper for Zendesk's official customer showcase pages.
    Extracts company names and information from customer stories.
    """

    def __init__(self, urls, request_delay=2.0, use_cloudscraper=True):
        """
        Initialize the Zendesk showcase scraper.

        Args:
            urls (list): List of Zendesk customer page URLs to scrape
            request_delay (float): Delay between requests in seconds
            use_cloudscraper (bool): Use cloudscraper for anti-bot bypassing
        """
        self.urls = urls if isinstance(urls, list) else [urls]
        self.request_delay = request_delay
        self.use_cloudscraper = use_cloudscraper and USE_CLOUDSCRAPER
        self.ua = UserAgent()

        # Initialize session
        if self.use_cloudscraper:
            self.session = cloudscraper.create_scraper()
        else:
            self.session = requests.Session()

    def _get_headers(self):
        """
        Generate request headers with random user agent.

        Returns:
            dict: HTTP headers
        """
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def scrape_customer_page(self, url):
        """
        Scrape a single Zendesk customer page.

        Args:
            url (str): URL of the customer page

        Returns:
            list: List of company dictionaries
        """
        companies = []

        try:
            print(f"\nScraping Zendesk customer page...")
            print(f"URL: {url}")

            # Make request
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try multiple strategies to find customer information

            # Strategy 1: Look for customer logos with alt text
            logo_images = soup.find_all('img', alt=True)
            for img in logo_images:
                alt_text = img.get('alt', '').strip()
                if alt_text and len(alt_text) > 2 and len(alt_text) < 50:
                    # Filter out common non-company alt text
                    if not any(skip in alt_text.lower() for skip in [
                        'icon', 'logo', 'image', 'photo', 'zendesk',
                        'screenshot', 'banner', 'hero'
                    ]):
                        company = {
                            'name': alt_text,
                            'source': 'Zendesk Customer Showcase',
                            'uses_zendesk': True,
                            'verified': True
                        }
                        companies.append(company)

            # Strategy 2: Look for customer cards or sections
            customer_cards = soup.select('div.customer-card, div.customer-story, article.customer')
            for card in customer_cards:
                company = self._extract_company_from_element(card)
                if company:
                    companies.append(company)

            # Strategy 3: Look for links to customer stories
            story_links = soup.find_all('a', href=re.compile(r'/customer|/story|/case-study'))
            for link in story_links:
                text = link.get_text(strip=True)
                if text and len(text) > 2 and len(text) < 50:
                    # Clean up the text
                    text = re.sub(r'\s+', ' ', text)
                    if not any(skip in text.lower() for skip in [
                        'read more', 'learn more', 'view', 'see how',
                        'customer stories', 'case studies'
                    ]):
                        company = {
                            'name': text,
                            'source': 'Zendesk Customer Showcase',
                            'uses_zendesk': True,
                            'verified': True
                        }
                        companies.append(company)

            # Strategy 4: Look for company names in text
            # Find elements that might contain company names
            potential_elements = soup.select(
                'h2, h3, h4, .company-name, .customer-name, [class*="company"], [class*="customer"]'
            )
            for elem in potential_elements:
                text = elem.get_text(strip=True)
                if text and 5 < len(text) < 50:
                    # Basic validation
                    if not any(skip in text.lower() for skip in [
                        'customer', 'story', 'stories', 'case study',
                        'learn', 'read', 'see how', 'featured'
                    ]):
                        company = {
                            'name': text,
                            'source': 'Zendesk Customer Showcase',
                            'uses_zendesk': True,
                            'verified': True
                        }
                        companies.append(company)

            print(f"Extracted {len(companies)} potential companies from showcase")

        except Exception as e:
            print(f"ERROR: Failed to scrape {url}: {str(e)}")

        return companies

    def _extract_company_from_element(self, element):
        """
        Extract company information from a DOM element.

        Args:
            element: BeautifulSoup element

        Returns:
            dict: Company information or None
        """
        try:
            company_data = {
                'source': 'Zendesk Customer Showcase',
                'uses_zendesk': True,
                'verified': True
            }

            # Try to find company name
            # Look for various possible selectors
            name_selectors = [
                'h2', 'h3', 'h4',
                '.company-name', '.customer-name',
                'a[href*="/customer"]', 'a[href*="/story"]'
            ]

            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name and len(name) > 2:
                        company_data['name'] = name
                        return company_data

            return None

        except Exception:
            return None

    def scrape_all_pages(self):
        """
        Scrape all configured Zendesk customer pages.

        Returns:
            list: Combined list of companies from all pages
        """
        all_companies = []

        print(f"\n{'='*60}")
        print(f"Starting Zendesk showcase scraping: {len(self.urls)} URLs")
        print(f"{'='*60}")

        for i, url in enumerate(self.urls, 1):
            # Scrape page
            companies = self.scrape_customer_page(url)
            all_companies.extend(companies)

            # Progress update
            print(f"Progress: {i}/{len(self.urls)} URLs complete, {len(all_companies)} companies found")

            # Delay before next request (except on last URL)
            if i < len(self.urls) and self.request_delay > 0:
                print(f"Waiting {self.request_delay} seconds before next request...")
                time.sleep(self.request_delay)

        # Deduplicate
        all_companies = self._deduplicate(all_companies)

        print(f"\n{'='*60}")
        print(f"Zendesk showcase scraping complete!")
        print(f"Total unique companies: {len(all_companies)}")
        print(f"{'='*60}\n")

        return all_companies

    def _deduplicate(self, companies):
        """
        Remove duplicate companies from list.

        Args:
            companies (list): List of company dictionaries

        Returns:
            list: Deduplicated list of companies
        """
        seen = set()
        unique_companies = []

        for company in companies:
            # Normalize company name for comparison
            company_key = company['name'].lower().strip()
            company_key = re.sub(r'\s+', ' ', company_key)

            if company_key and company_key not in seen:
                # Additional validation: company name should be reasonable
                if self._is_valid_company_name(company['name']):
                    seen.add(company_key)
                    unique_companies.append(company)

        duplicates_removed = len(companies) - len(unique_companies)
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate/invalid companies")

        return unique_companies

    def _is_valid_company_name(self, name):
        """
        Validate that the extracted name is likely a real company name.

        Args:
            name (str): Company name to validate

        Returns:
            bool: True if valid company name
        """
        if not name or len(name) < 2:
            return False

        # Too long is suspicious
        if len(name) > 60:
            return False

        # Should not be mostly numbers
        if sum(c.isdigit() for c in name) > len(name) / 2:
            return False

        # Skip common false positives
        skip_patterns = [
            r'^read\s+more',
            r'^learn\s+more',
            r'^view\s+',
            r'^see\s+how',
            r'customer\s+stor',
            r'case\s+stud',
            r'^featured',
            r'^\d+$',  # Just numbers
            r'^[^\w\s]+$',  # Just special characters
        ]

        name_lower = name.lower()
        for pattern in skip_patterns:
            if re.search(pattern, name_lower):
                return False

        return True


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("ZENDESK SHOWCASE SCRAPER TEST")
    print("=" * 80)

    # Test configuration
    ZENDESK_URLS = [
        "https://www.zendesk.com/customers/",
        "https://www.zendesk.com/customer-stories/",
    ]

    try:
        # Initialize scraper
        scraper = ZendeskShowcaseScraper(ZENDESK_URLS, request_delay=2.0)

        # Test scraping
        print("\nTesting Zendesk showcase scraping...")
        companies = scraper.scrape_all_pages()

        if companies:
            print(f"\nFound {len(companies)} unique companies")
            print("\nSample companies:")
            for i, company in enumerate(companies[:10], 1):
                print(f"  {i}. {company['name']}")
        else:
            print("\nNo companies found. This could be due to:")
            print("  1. Zendesk changed their website structure")
            print("  2. Anti-bot protection blocked the request")
            print("  3. Network issues")
            print("\nNote: Zendesk showcase scraping may yield fewer results")
            print("      than other sources. This is expected.")

    except Exception as e:
        print(f"\nERROR during test: {str(e)}")

    print("\n" + "=" * 80)
