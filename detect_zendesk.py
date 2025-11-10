"""
Zendesk Detection Module

Two-stage detection system:
1. Fast HTML heuristic checks (requests + BeautifulSoup)
2. JavaScript-rendered fallback (Playwright for headless browser)

Scoring based on weighted signals with configurable threshold.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import yaml
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZendeskDetector:
    """
    Detects Zendesk usage on company websites using a two-stage approach.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the detector with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.weights = self.config['detection']['weights']
        self.threshold = self.config['detection']['threshold']
        self.timeout = self.config['http']['timeout']
        self.user_agent = self.config['http']['user_agent']

        logger.info(f"Initialized ZendeskDetector with threshold={self.threshold}")

    def detect(self, domain: str) -> Dict:
        """
        Main detection method - combines fast check and optional Playwright fallback.

        Args:
            domain: Company domain (e.g., 'shopify.com')

        Returns:
            dict: {
                'domain': str,
                'detected': bool,
                'score': int,
                'signals': dict,
                'method': str,  # 'fast' or 'playwright'
                'timestamp': str
            }
        """
        logger.info(f"Detecting Zendesk on {domain}")

        # Stage 1: Fast HTML check
        fast_result = self.fast_check(domain)

        # Check if we need Playwright fallback
        fallback_min = self.config['detection']['playwright_fallback_min']
        fallback_max = self.config['detection']['playwright_fallback_max']

        if fallback_min <= fast_result['score'] <= fallback_max:
            logger.info(f"{domain}: Fast check score {fast_result['score']}, running Playwright fallback")
            playwright_result = self.playwright_check(domain)

            # Combine signals from both methods
            combined_signals = {**fast_result['signals'], **playwright_result['signals']}
            combined_score = self._calculate_score(combined_signals)

            return {
                'domain': domain,
                'detected': combined_score >= self.threshold,
                'score': combined_score,
                'signals': combined_signals,
                'method': 'combined',
                'timestamp': datetime.utcnow().isoformat()
            }

        # Fast check was conclusive
        return {
            'domain': domain,
            'detected': fast_result['detected'],
            'score': fast_result['score'],
            'signals': fast_result['signals'],
            'method': 'fast',
            'timestamp': datetime.utcnow().isoformat()
        }

    def fast_check(self, domain: str) -> Dict:
        """
        Fast HTML-based detection using requests and BeautifulSoup.

        Checks for:
        - Script tags with zendesk.com or zdassets.com
        - Links to help.*.zendesk.com
        - /hc/ paths in URLs
        - Zendesk cookies in response headers
        - DOM classes containing 'zendesk'

        Args:
            domain: Company domain

        Returns:
            dict: Detection result with signals
        """
        signals = {}
        url = f"https://{domain}"

        try:
            # Make HTTP request
            headers = {'User-Agent': self.user_agent}
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Check 1: Script tags
            for script in soup.find_all('script', src=True):
                src = script['src'].lower()
                if 'zendesk.com' in src or 'assets.zendesk' in src:
                    signals['script_zendesk'] = True
                if 'zdassets.com' in src or 'zdcdn' in src:
                    signals['cdn_zdassets'] = True

            # Check 2: Links to Zendesk help pages
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                if '.zendesk.com' in href:
                    if 'help.' in href or 'support.' in href:
                        signals['help_subdomain_link'] = True
                if '/hc/' in href:
                    signals['hc_path'] = True

            # Check 3: Cookies
            if 'set-cookie' in response.headers:
                cookies = response.headers['set-cookie'].lower()
                if 'zendesk' in cookies or 'zd_' in cookies:
                    signals['cookie_zendesk'] = True

            # Check 4: DOM classes
            for elem in soup.find_all(class_=True):
                classes = ' '.join(elem['class']).lower()
                if 'zendesk' in classes or 'zopim' in classes or 'zd-widget' in classes:
                    signals['dom_class_zendesk'] = True
                    break

            # Calculate score
            score = self._calculate_score(signals)

            logger.info(f"{domain}: Fast check found {len(signals)} signals, score={score}")

            return {
                'domain': domain,
                'detected': score >= self.threshold,
                'score': score,
                'signals': signals
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"{domain}: Fast check failed - {str(e)}")
            return {
                'domain': domain,
                'detected': False,
                'score': 0,
                'signals': {},
                'error': str(e)
            }

    def playwright_check(self, domain: str) -> Dict:
        """
        JavaScript-rendered detection using Playwright.

        Checks for:
        - window.zE, window.Zendesk, window.Zopim globals
        - Network requests to zendesk.com or zdassets.com
        - DOM elements after JS rendering

        Args:
            domain: Company domain

        Returns:
            dict: Detection result with additional JS-based signals
        """
        signals = {}

        try:
            # Import Playwright only when needed
            from playwright.sync_api import sync_playwright

            url = f"https://{domain}"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Track network requests
                network_requests = []

                def handle_request(request):
                    network_requests.append(request.url)

                page.on('request', handle_request)

                # Navigate to page
                page.goto(url, wait_until='networkidle', timeout=30000)

                # Check for window globals
                window_ze = page.evaluate('() => typeof window.zE !== "undefined"')
                window_zendesk = page.evaluate('() => typeof window.Zendesk !== "undefined"')
                window_zopim = page.evaluate('() => typeof window.Zopim !== "undefined"')

                if window_ze:
                    signals['window_ze'] = True
                if window_zendesk:
                    signals['window_zendesk'] = True
                if window_zopim:
                    signals['window_zendesk'] = True  # Zopim is Zendesk Chat

                # Check network requests
                for req_url in network_requests:
                    if 'zendesk.com' in req_url or 'zdassets.com' in req_url:
                        signals['xhr_zendesk'] = True
                        break

                # Re-check DOM after JS render
                html = page.content()
                if 'zendesk' in html.lower() or 'zd-widget' in html.lower():
                    signals['dom_class_zendesk'] = True

                browser.close()

            score = self._calculate_score(signals)

            logger.info(f"{domain}: Playwright check found {len(signals)} signals, score={score}")

            return {
                'domain': domain,
                'detected': score >= self.threshold,
                'score': score,
                'signals': signals
            }

        except Exception as e:
            logger.warning(f"{domain}: Playwright check failed - {str(e)}")
            return {
                'domain': domain,
                'detected': False,
                'score': 0,
                'signals': {},
                'error': str(e)
            }

    def _calculate_score(self, signals: Dict) -> int:
        """
        Calculate detection score based on weighted signals.

        Args:
            signals: Dictionary of detected signals

        Returns:
            int: Total score
        """
        score = 0
        for signal_name, detected in signals.items():
            if detected and signal_name in self.weights:
                score += self.weights[signal_name]

        return score


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    import sys

    # Test on a known Zendesk user
    detector = ZendeskDetector()

    test_domains = [
        "shopify.com",      # Known Zendesk user
        "stripe.com",       # Known Zendesk user
        "google.com",       # Not using Zendesk (probably)
    ]

    for domain in test_domains:
        print(f"\n{'='*60}")
        print(f"Testing: {domain}")
        print('='*60)

        result = detector.fast_check(domain)

        print(f"Detected: {result['detected']}")
        print(f"Score: {result['score']}")
        print(f"Signals: {result['signals']}")

        if result['score'] > 0 and result['score'] < 100:
            print(f"\nRunning Playwright fallback...")
            full_result = detector.detect(domain)
            print(f"Final detected: {full_result['detected']}")
            print(f"Final score: {full_result['score']}")
