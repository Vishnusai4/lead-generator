"""
Zendesk Detection Module with Escalation Logic

Implements a three-tier detection system:
1. Fast HTML check (requests)
2. Cloudscraper (for Cloudflare bypass)
3. Playwright (full browser automation)

Automatically escalates when bot-blocking detected (403, 406, 429).
"""

import re
import logging
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import yaml

# Try to import optional dependencies
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class ZendeskDetector:
    """
    Detects Zendesk usage with automatic escalation on bot-blocking.
    """

    # Status codes that indicate bot-blocking
    BLOCKING_STATUS_CODES = {403, 406, 429, 503}

    def __init__(self, config_path: str = "config.yaml", use_cloudscraper: bool = False,
                 use_playwright: bool = False, no_escalation: bool = False):
        """
        Initialize detector with configuration.

        Args:
            config_path: Path to YAML configuration
            use_cloudscraper: Enable cloudscraper for Cloudflare bypass
            use_playwright: Force Playwright for all domains
            no_escalation: Disable automatic escalation
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.weights = self.config['detection']['weights']
        self.threshold = self.config['detection']['threshold']
        self.timeout = self.config['http']['timeout']
        self.user_agent = self.config['http']['user_agent']

        self.use_cloudscraper = use_cloudscraper and CLOUDSCRAPER_AVAILABLE
        self.force_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        self.no_escalation = no_escalation

        logger.info(f"Initialized detector: threshold={self.threshold}, "
                   f"cloudscraper={self.use_cloudscraper}, playwright={PLAYWRIGHT_AVAILABLE}")

    def detect(self, domain: str) -> Dict:
        """
        Main detection with automatic escalation.

        Escalation order:
        1. Fast requests check
        2. If blocked (403/406/429) → try cloudscraper (if enabled)
        3. If still blocked or score in threshold range → try Playwright

        Args:
            domain: Company domain

        Returns:
            dict: Detection results with escalation metadata
        """
        logger.info(f"Starting detection for {domain}")

        # Force Playwright mode
        if self.force_playwright:
            logger.info(f"{domain}: Force Playwright mode enabled")
            return self._detect_with_playwright(domain, method='playwright_forced')

        # Stage 1: Fast requests check
        fast_result = self._fast_check(domain)

        # Check if we got blocked
        blocked = fast_result.get('blocked_by_waf', False)
        original_status = fast_result.get('original_status_code', 200)

        # Log blocking event
        if blocked:
            self._log_blocking_event(domain, original_status, fast_result.get('original_headers', {}))

        # Decide on escalation
        if self.no_escalation:
            logger.info(f"{domain}: No escalation mode, returning fast check result")
            return fast_result

        # Escalation logic
        should_escalate = False

        # Escalate if blocked
        if blocked:
            should_escalate = True
            logger.warning(f"{domain}: Blocked (status {original_status}), escalating")

        # Escalate if score is in the threshold range
        elif 0 < fast_result['score'] < self.threshold:
            should_escalate = True
            logger.info(f"{domain}: Score {fast_result['score']} in threshold range, escalating")

        if not should_escalate:
            logger.info(f"{domain}: No escalation needed (score={fast_result['score']})")
            return fast_result

        # Stage 2: Try cloudscraper (if enabled and blocked)
        if self.use_cloudscraper and blocked:
            logger.info(f"{domain}: Attempting cloudscraper bypass")
            cloudscraper_result = self._cloudscraper_check(domain)

            # If cloudscraper succeeded and wasn't blocked
            if not cloudscraper_result.get('blocked_by_waf', False):
                logger.info(f"{domain}: Cloudscraper bypass successful")
                return cloudscraper_result

            logger.info(f"{domain}: Cloudscraper also blocked, trying Playwright")

        # Stage 3: Playwright fallback
        if PLAYWRIGHT_AVAILABLE:
            logger.info(f"{domain}: Running Playwright check")
            playwright_result = self._detect_with_playwright(domain, method='playwright_escalated')

            # Combine signals from fast check and Playwright
            combined_signals = {**fast_result.get('signals', {}), **playwright_result.get('signals', {})}
            playwright_result['signals'] = combined_signals
            playwright_result['score'] = self._calculate_score(combined_signals)
            playwright_result['detected'] = playwright_result['score'] >= self.threshold

            return playwright_result
        else:
            logger.warning(f"{domain}: Playwright not available, returning fast check result")
            return fast_result

    def _fast_check(self, domain: str) -> Dict:
        """
        Fast HTML check using requests.

        Returns:
            dict: Detection result with blocking metadata
        """
        signals = {}
        url = f"https://{domain}"
        blocked_by_waf = False
        original_status_code = None
        original_headers = {}

        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)

            original_status_code = response.status_code
            original_headers = dict(response.headers)

            # Check if blocked
            if response.status_code in self.BLOCKING_STATUS_CODES:
                blocked_by_waf = True
                logger.warning(f"{domain}: Blocked with status {response.status_code}")

                return {
                    'domain': domain,
                    'detected': False,
                    'score': 0,
                    'signals': {},
                    'method': 'fast_blocked',
                    'blocked_by_waf': True,
                    'original_status_code': original_status_code,
                    'original_headers': json.dumps(original_headers),
                    'timestamp': datetime.utcnow().isoformat()
                }

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

            # Check 2: Links
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

            score = self._calculate_score(signals)

            logger.info(f"{domain}: Fast check - {len(signals)} signals, score={score}")

            return {
                'domain': domain,
                'detected': score >= self.threshold,
                'score': score,
                'signals': signals,
                'method': 'fast',
                'blocked_by_waf': False,
                'original_status_code': original_status_code,
                'original_headers': json.dumps(original_headers),
                'timestamp': datetime.utcnow().isoformat()
            }

        except requests.exceptions.RequestException as e:
            logger.warning(f"{domain}: Request failed - {str(e)}")
            return {
                'domain': domain,
                'detected': False,
                'score': 0,
                'signals': {},
                'method': 'fast_error',
                'blocked_by_waf': False,
                'original_status_code': original_status_code or 0,
                'original_headers': json.dumps(original_headers),
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _cloudscraper_check(self, domain: str) -> Dict:
        """
        Check using cloudscraper to bypass Cloudflare.

        Returns:
            dict: Detection result
        """
        if not CLOUDSCRAPER_AVAILABLE:
            return {'blocked_by_waf': True, 'error': 'Cloudscraper not available'}

        signals = {}
        url = f"https://{domain}"

        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=self.timeout)

            if response.status_code in self.BLOCKING_STATUS_CODES:
                logger.warning(f"{domain}: Cloudscraper also blocked ({response.status_code})")
                return {
                    'domain': domain,
                    'detected': False,
                    'score': 0,
                    'signals': {},
                    'method': 'cloudscraper_blocked',
                    'blocked_by_waf': True,
                    'original_status_code': response.status_code,
                    'original_headers': json.dumps(dict(response.headers)),
                    'timestamp': datetime.utcnow().isoformat()
                }

            # Parse HTML (same logic as fast check)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Reuse signal detection logic
            for script in soup.find_all('script', src=True):
                src = script['src'].lower()
                if 'zendesk.com' in src:
                    signals['script_zendesk'] = True
                if 'zdassets.com' in src:
                    signals['cdn_zdassets'] = True

            score = self._calculate_score(signals)

            return {
                'domain': domain,
                'detected': score >= self.threshold,
                'score': score,
                'signals': signals,
                'method': 'cloudscraper',
                'blocked_by_waf': False,
                'original_status_code': response.status_code,
                'original_headers': json.dumps(dict(response.headers)),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.warning(f"{domain}: Cloudscraper failed - {str(e)}")
            return {'blocked_by_waf': True, 'error': str(e)}

    def _detect_with_playwright(self, domain: str, method: str = 'playwright') -> Dict:
        """
        Playwright-based detection (full browser).

        Args:
            domain: Domain to check
            method: Method name for logging

        Returns:
            dict: Detection result
        """
        signals = {}
        url = f"https://{domain}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.user_agent)

                # Track network requests
                network_requests = []
                def handle_request(request):
                    network_requests.append(request.url)
                page.on('request', handle_request)

                # Navigate
                try:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                except Exception as nav_error:
                    logger.warning(f"{domain}: Playwright navigation failed - {str(nav_error)}")
                    browser.close()
                    return {
                        'domain': domain,
                        'detected': False,
                        'score': 0,
                        'signals': {},
                        'method': f'{method}_error',
                        'blocked_by_waf': True,
                        'error': str(nav_error),
                        'timestamp': datetime.utcnow().isoformat()
                    }

                # Check window globals
                if page.evaluate('() => typeof window.zE !== "undefined"'):
                    signals['window_ze'] = True
                if page.evaluate('() => typeof window.Zendesk !== "undefined"'):
                    signals['window_zendesk'] = True

                # Check network requests
                for req_url in network_requests:
                    if 'zendesk.com' in req_url or 'zdassets.com' in req_url:
                        signals['xhr_zendesk'] = True
                        break

                # Check DOM
                html = page.content().lower()
                if 'zendesk' in html or 'zd-widget' in html:
                    signals['dom_class_zendesk'] = True

                browser.close()

            score = self._calculate_score(signals)

            logger.info(f"{domain}: Playwright - {len(signals)} signals, score={score}")

            return {
                'domain': domain,
                'detected': score >= self.threshold,
                'score': score,
                'signals': signals,
                'method': method,
                'blocked_by_waf': False,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"{domain}: Playwright error - {str(e)}")
            return {
                'domain': domain,
                'detected': False,
                'score': 0,
                'signals': {},
                'method': f'{method}_error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _calculate_score(self, signals: Dict) -> int:
        """Calculate score from signals."""
        score = 0
        for signal_name, detected in signals.items():
            if detected and signal_name in self.weights:
                score += self.weights[signal_name]
        return score

    def _log_blocking_event(self, domain: str, status_code: int, headers: dict):
        """
        Log structured blocking event.

        Args:
            domain: Blocked domain
            status_code: HTTP status code
            headers: Response headers
        """
        event = {
            'event': 'blocked_by_waf',
            'timestamp': datetime.utcnow().isoformat(),
            'domain': domain,
            'status_code': status_code,
            'headers': headers,
            'suggested_actions': [
                'Try --use-cloudscraper flag',
                'Try --use-playwright flag',
                'Use residential proxies with --proxy-file',
                'Manual review may be needed'
            ]
        }

        logger.warning(f"BLOCKED: {json.dumps(event)}")
