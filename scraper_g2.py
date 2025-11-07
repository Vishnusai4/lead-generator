"""
G2 Reviews Scraper

This module scrapes G2.com review pages to identify companies using Zendesk.
G2 reviews often include company information like company name, size, and industry.

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


class G2Scraper:
    """
    Scraper for G2.com Zendesk review pages.
    Extracts company information from reviewer profiles.
    """

    def __init__(self, base_url, request_delay=2.0, use_cloudscraper=True):
        """
        Initialize the G2 scraper.

        Args:
            base_url (str): Base URL for G2 Zendesk reviews
            request_delay (float): Delay between requests in seconds
            use_cloudscraper (bool): Use cloudscraper for anti-bot bypassing
        """
        self.base_url = base_url
        self.request_delay = request_delay
        self.use_cloudscraper = use_cloudscraper and USE_CLOUDSCRAPER
        self.ua = UserAgent()

        # Initialize session
        if self.use_cloudscraper:
            self.session = cloudscraper.create_scraper()
            print("Using cloudscraper for anti-bot bypassing")
        else:
            self.session = requests.Session()
            print("Using standard requests library")

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
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def scrape_reviews_page(self, page_num=1):
        """
        Scrape a single page of G2 reviews.

        Args:
            page_num (int): Page number to scrape

        Returns:
            list: List of company dictionaries
        """
        companies = []

        try:
            # Construct URL with page parameter
            if page_num > 1:
                url = f"{self.base_url}?page={page_num}"
            else:
                url = self.base_url

            print(f"\nScraping G2 page {page_num}...")
            print(f"URL: {url}")

            # Make request
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find review cards
            # G2 structure varies, so we'll try multiple selectors
            review_cards = []

            # Try different possible selectors
            selectors = [
                'div[data-review-id]',
                'div.paper.paper--white',
                'div.review-card',
                'div[class*="review"]',
                'article'
            ]

            for selector in selectors:
                review_cards = soup.select(selector)
                if review_cards:
                    print(f"Found {len(review_cards)} review cards using selector: {selector}")
                    break

            if not review_cards:
                print("WARNING: No review cards found on this page")
                return companies

            # Extract company info from each review
            for card in review_cards:
                company = self._extract_company_from_card(card)
                if company:
                    companies.append(company)

            print(f"Extracted {len(companies)} companies from page {page_num}")

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to fetch page {page_num}: {str(e)}")
        except Exception as e:
            print(f"ERROR: Failed to parse page {page_num}: {str(e)}")

        return companies

    def _extract_company_from_card(self, card):
        """
        Extract company information from a review card.

        Args:
            card: BeautifulSoup element containing review data

        Returns:
            dict: Company information or None if extraction failed
        """
        try:
            company_data = {
                'name': '',
                'industry': '',
                'company_size': '',
                'source': 'G2 Reviews',
                'uses_zendesk': True
            }

            # Extract company name
            # Try multiple possible locations for company name
            name_selectors = [
                ('div.source-company', 'text'),
                ('span.company-name', 'text'),
                ('div[class*="company"]', 'text'),
                ('a[href*="/company/"]', 'text'),
            ]

            for selector, attr_type in name_selectors:
                element = card.select_one(selector)
                if element:
                    company_data['name'] = element.get_text(strip=True)
                    break

            # Extract industry
            industry_selectors = [
                ('div.source-industry', 'text'),
                ('span[class*="industry"]', 'text'),
                ('div[class*="vertical"]', 'text'),
            ]

            for selector, attr_type in industry_selectors:
                element = card.select_one(selector)
                if element:
                    company_data['industry'] = element.get_text(strip=True)
                    break

            # Extract company size
            size_selectors = [
                ('div.source-company-size', 'text'),
                ('span[class*="company-size"]', 'text'),
                ('div[class*="size"]', 'text'),
            ]

            for selector, attr_type in size_selectors:
                element = card.select_one(selector)
                if element:
                    size_text = element.get_text(strip=True)
                    company_data['company_size'] = self._normalize_company_size(size_text)
                    break

            # Only return if we found at least a company name
            if company_data['name']:
                return company_data

            return None

        except Exception as e:
            # Silently skip problematic cards
            return None

    def _normalize_company_size(self, size_text):
        """
        Normalize company size text to standard format.

        Args:
            size_text (str): Raw company size text

        Returns:
            str: Normalized company size
        """
        if not size_text:
            return ''

        size_lower = size_text.lower()

        # Extract number ranges
        numbers = re.findall(r'\d+', size_text)

        if 'small' in size_lower or (numbers and int(numbers[0]) < 50):
            return 'Small Business (1-50)'
        elif 'mid' in size_lower or (numbers and 50 <= int(numbers[0]) < 200):
            return 'Mid-Market (51-200)'
        elif 'enterprise' in size_lower or (numbers and int(numbers[0]) >= 200):
            return 'Enterprise (200+)'
        else:
            return size_text

    def scrape_multiple_pages(self, num_pages=5):
        """
        Scrape multiple pages of G2 reviews.

        Args:
            num_pages (int): Number of pages to scrape

        Returns:
            list: Combined list of companies from all pages
        """
        all_companies = []

        print(f"\n{'='*60}")
        print(f"Starting G2 scraping: {num_pages} pages")
        print(f"{'='*60}")

        for page in range(1, num_pages + 1):
            # Scrape page
            companies = self.scrape_reviews_page(page)
            all_companies.extend(companies)

            # Progress update
            print(f"Progress: {page}/{num_pages} pages complete, {len(all_companies)} companies found")

            # Delay before next request (except on last page)
            if page < num_pages and self.request_delay > 0:
                print(f"Waiting {self.request_delay} seconds before next request...")
                time.sleep(self.request_delay)

        # Deduplicate
        all_companies = self._deduplicate(all_companies)

        print(f"\n{'='*60}")
        print(f"G2 scraping complete!")
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
            company_key = company['name'].lower().strip()
            if company_key and company_key not in seen:
                seen.add(company_key)
                unique_companies.append(company)

        duplicates_removed = len(companies) - len(unique_companies)
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate companies")

        return unique_companies


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("G2 SCRAPER TEST")
    print("=" * 80)

    # Test configuration
    G2_URL = "https://www.g2.com/products/zendesk/reviews"

    try:
        # Initialize scraper
        scraper = G2Scraper(G2_URL, request_delay=2.0)

        # Test scraping single page
        print("\nTesting single page scrape...")
        companies = scraper.scrape_reviews_page(1)

        if companies:
            print(f"\nFound {len(companies)} companies on page 1")
            print("\nSample companies:")
            for i, company in enumerate(companies[:5], 1):
                print(f"\n{i}. {company['name']}")
                print(f"   Industry: {company.get('industry', 'N/A')}")
                print(f"   Size: {company.get('company_size', 'N/A')}")
        else:
            print("\nNo companies found. This could be due to:")
            print("  1. G2 changed their HTML structure")
            print("  2. Anti-bot protection blocked the request")
            print("  3. Network issues")
            print("\nThe scraper may need updates to work with current G2 structure.")

    except Exception as e:
        print(f"\nERROR during test: {str(e)}")

    print("\n" + "=" * 80)
