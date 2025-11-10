#!/usr/bin/env python3
"""
Zendesk Lead Generation Pipeline

Production-ready CLI for detecting Zendesk usage and enriching company data.

Features:
- Multi-threaded processing
- Automatic escalation (requests → cloudscraper → Playwright)
- Company enrichment with US filtering
- SQLite + CSV persistence
- Comprehensive logging and progress tracking
"""

import argparse
import csv
import logging
import os
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

from detect_zendesk import ZendeskDetector
from enrichment import CompanyEnricher
from storage import LeadStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class LeadPipeline:
    """
    Main pipeline coordinator.

    Orchestrates detection, enrichment, and storage.
    """

    def __init__(self, args):
        """
        Initialize pipeline with CLI arguments.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args

        # Initialize detector
        self.detector = ZendeskDetector(
            config_path=args.config,
            use_cloudscraper=args.use_cloudscraper,
            use_playwright=args.use_playwright,
            no_escalation=args.no_escalation
        )

        # Initialize enricher (if not disabled)
        self.enricher = None
        if not args.no_enrichment:
            clearbit_key = os.getenv('CLEARBIT_API_KEY')
            self.enricher = CompanyEnricher(
                clearbit_api_key=clearbit_key,
                us_only=args.us_only
            )

        # Initialize storage
        self.storage = LeadStorage(
            db_path=args.db_path,
            csv_path=args.output
        )

        logger.info(f"Pipeline initialized: threads={args.threads}, "
                   f"enrichment={'enabled' if self.enricher else 'disabled'}, "
                   f"us_only={args.us_only}")

    def load_domains(self) -> List[str]:
        """
        Load domains from input CSV.

        Returns:
            list: List of domain strings
        """
        domains = []

        with open(self.args.input, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                domain = row.get('domain', '').strip()
                if domain:
                    domains.append(domain)

        logger.info(f"Loaded {len(domains)} domains from {self.args.input}")
        return domains

    def process_domain(self, domain: str) -> Dict:
        """
        Process a single domain through detection and enrichment.

        Args:
            domain: Company domain

        Returns:
            dict: Combined detection and enrichment data
        """
        try:
            # Rate limiting
            if self.args.rate_limit > 0:
                time.sleep(1.0 / self.args.rate_limit)

            # Stage 1: Detect Zendesk
            logger.info(f"Processing {domain}...")
            detection_result = self.detector.detect(domain)

            # Prepare lead data
            lead_data = {
                'domain': domain,
                'detected_zendesk': detection_result.get('detected', False),
                'zendesk_score': detection_result.get('score', 0),
                'signals': detection_result.get('signals', {}),
                'detection_timestamp': detection_result.get('timestamp'),
                'blocked_by_waf': detection_result.get('blocked_by_waf', False),
                'original_status_code': detection_result.get('original_status_code'),
                'original_headers': detection_result.get('original_headers'),
                'detection_method': detection_result.get('method', 'unknown'),
                'error': detection_result.get('error')
            }

            # Stage 2: Enrichment (if enabled and not blocked)
            if self.enricher and not lead_data['blocked_by_waf']:
                enriched = self.enricher.enrich(domain)

                if enriched:
                    lead_data.update(enriched)
                    logger.info(f"{domain}: Enriched successfully")
                elif self.args.us_only:
                    # Filtered out due to non-US location
                    logger.info(f"{domain}: Skipped (non-US)")
                    return None
                else:
                    logger.warning(f"{domain}: Enrichment failed")

            return lead_data

        except Exception as e:
            logger.error(f"{domain}: Processing failed - {str(e)}")
            return {
                'domain': domain,
                'detected_zendesk': False,
                'zendesk_score': 0,
                'signals': {},
                'detection_timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    def run(self):
        """Execute the full pipeline."""
        start_time = time.time()

        print("=" * 80)
        print("ZENDESK LEAD GENERATION PIPELINE")
        print("=" * 80)
        print(f"\nConfiguration:")
        print(f"  Input: {self.args.input}")
        print(f"  Output: {self.args.output}")
        print(f"  Database: {self.args.db_path}")
        print(f"  Threads: {self.args.threads}")
        print(f"  Enrichment: {'Enabled' if self.enricher else 'Disabled'}")
        print(f"  US-only: {self.args.us_only}")
        print(f"  Cloudscraper: {self.args.use_cloudscraper}")
        print(f"  Playwright: {self.args.use_playwright}")
        print(f"  Rate limit: {self.args.rate_limit} req/sec")
        print()

        # Load domains
        domains = self.load_domains()

        if not domains:
            logger.error("No domains to process")
            return

        # Process domains
        results = []
        processed = 0
        detected = 0
        enriched = 0
        blocked = 0
        filtered = 0

        print(f"Processing {len(domains)} domains...\n")

        if self.args.threads > 1:
            # Multi-threaded processing
            with ThreadPoolExecutor(max_workers=self.args.threads) as executor:
                futures = {
                    executor.submit(self.process_domain, domain): domain
                    for domain in domains
                }

                for future in as_completed(futures):
                    domain = futures[future]
                    processed += 1

                    try:
                        result = future.result()

                        if result is None:
                            # Filtered out
                            filtered += 1
                            logger.info(f"[{processed}/{len(domains)}] {domain}: Filtered out")
                            continue

                        results.append(result)

                        # Update counters
                        if result.get('detected_zendesk'):
                            detected += 1
                        if result.get('enriched_at'):
                            enriched += 1
                        if result.get('blocked_by_waf'):
                            blocked += 1

                        status = "✓ DETECTED" if result['detected_zendesk'] else "✗ Not detected"
                        if result.get('blocked_by_waf'):
                            status += " (BLOCKED)"

                        print(f"[{processed}/{len(domains)}] {domain}: {status} "
                              f"(score: {result.get('zendesk_score', 0)})")

                    except Exception as e:
                        logger.error(f"[{processed}/{len(domains)}] {domain}: ERROR - {str(e)}")

        else:
            # Single-threaded processing
            for i, domain in enumerate(domains, 1):
                processed += 1

                result = self.process_domain(domain)

                if result is None:
                    # Filtered out
                    filtered += 1
                    logger.info(f"[{i}/{len(domains)}] {domain}: Filtered out")
                    continue

                results.append(result)

                # Update counters
                if result.get('detected_zendesk'):
                    detected += 1
                if result.get('enriched_at'):
                    enriched += 1
                if result.get('blocked_by_waf'):
                    blocked += 1

                status = "✓ DETECTED" if result['detected_zendesk'] else "✗ Not detected"
                if result.get('blocked_by_waf'):
                    status += " (BLOCKED)"

                print(f"[{i}/{len(domains)}] {domain}: {status} "
                      f"(score: {result.get('zendesk_score', 0)})")

        # Save results
        print(f"\nSaving {len(results)} results...")
        save_stats = self.storage.batch_save(results)

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Print summary
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)
        print(f"\nProcessing Statistics:")
        print(f"  Total domains: {len(domains)}")
        print(f"  Processed: {processed}")
        print(f"  Filtered (non-US): {filtered}")
        print(f"  Saved to database: {save_stats['saved']}")
        print(f"  Updated in database: {save_stats['updated']}")
        print(f"  Failed: {save_stats['failed']}")
        print(f"\nDetection Results:")
        print(f"  ✓ Zendesk detected: {detected}")
        print(f"  ✗ Not detected: {len(results) - detected}")
        print(f"  Blocked by WAF: {blocked}")
        print(f"  Detection rate: {detected/len(results)*100:.1f}%" if results else "  Detection rate: 0%")
        print(f"\nEnrichment Results:")
        print(f"  Enriched: {enriched}")
        print(f"  Enrichment rate: {enriched/len(results)*100:.1f}%" if results else "  Enrichment rate: 0%")
        print(f"\nPerformance:")
        print(f"  Elapsed time: {elapsed_time:.1f}s")
        print(f"  Throughput: {len(domains)/elapsed_time:.2f} domains/sec")
        print(f"\nOutput:")
        print(f"  Database: {self.args.db_path}")
        print(f"  CSV: {self.args.output}")
        print("=" * 80)

        logger.info(f"Pipeline complete: {len(results)} results saved")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Zendesk Lead Generation Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python run_pipeline.py --input domains.csv

  # With enrichment and US-only filter
  python run_pipeline.py --input domains.csv --us-only

  # Force Playwright for all domains
  python run_pipeline.py --input domains.csv --use-playwright

  # Multi-threaded processing
  python run_pipeline.py --input domains.csv --threads 10

  # Disable enrichment for faster detection-only runs
  python run_pipeline.py --input domains.csv --no-enrichment
        """
    )

    # Input/Output
    parser.add_argument('--input', default='examples/seed.csv',
                        help='Input CSV with domain column (default: examples/seed.csv)')
    parser.add_argument('--output', default='leads.csv',
                        help='Output CSV path (default: leads.csv)')
    parser.add_argument('--db-path', default='leads.db',
                        help='SQLite database path (default: leads.db)')

    # Detection options
    parser.add_argument('--config', default='config.yaml',
                        help='Detection config path (default: config.yaml)')
    parser.add_argument('--use-cloudscraper', action='store_true',
                        help='Enable cloudscraper for Cloudflare bypass')
    parser.add_argument('--use-playwright', action='store_true',
                        help='Force Playwright for all domains')
    parser.add_argument('--no-escalation', action='store_true',
                        help='Disable automatic escalation on bot-blocking')
    parser.add_argument('--ignore-robots', action='store_true',
                        help='Ignore robots.txt (use with caution)')

    # Enrichment options
    parser.add_argument('--no-enrichment', action='store_true',
                        help='Disable company enrichment (detection only)')
    parser.add_argument('--us-only', action='store_true', default=True,
                        help='Only process US companies (default: True)')
    parser.add_argument('--all-countries', action='store_true',
                        help='Process companies from all countries')

    # Performance options
    parser.add_argument('--threads', type=int, default=1,
                        help='Number of concurrent threads (default: 1)')
    parser.add_argument('--rate-limit', type=float, default=1.0,
                        help='Requests per second (default: 1.0)')

    # Proxy support
    parser.add_argument('--proxy-file',
                        help='File with proxy list (one per line)')

    args = parser.parse_args()

    # Handle --all-countries flag
    if args.all_countries:
        args.us_only = False

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)

    # Initialize and run pipeline
    try:
        pipeline = LeadPipeline(args)
        pipeline.run()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
