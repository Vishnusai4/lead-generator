#!/usr/bin/env python3
"""
Zendesk Lead Finder - Main Pipeline

This is the main orchestrator for the lead generation system.
It coordinates scraping, enrichment, and CRM updates.

Usage:
    python main.py --mode full          # Full pipeline run
    python main.py --mode test          # Test run (limited data)
    python main.py --mode g2-only       # Only scrape G2
    python main.py --mode zendesk-only  # Only scrape Zendesk
    python main.py --no-enrich          # Skip enrichment step
"""

import sys
import argparse
from datetime import datetime

# Import our modules
try:
    import config
except ImportError:
    print("=" * 80)
    print("ERROR: config.py not found!")
    print("=" * 80)
    print("\nPlease create config.py from config_template.py:")
    print("  1. cp config_template.py config.py")
    print("  2. Edit config.py with your settings")
    print("  3. Run this script again")
    print("\n" + "=" * 80)
    sys.exit(1)

from sheets_crm import SheetsCRM
from scraper_g2 import G2Scraper
from scraper_zendesk import ZendeskShowcaseScraper
from enrichment import CompanyEnricher
from known_customers import get_known_customers


class LeadGenPipeline:
    """
    Main lead generation pipeline that orchestrates all components.
    """

    def __init__(self):
        """
        Initialize the lead generation pipeline.
        """
        print("\n" + "=" * 80)
        print(" " * 20 + "ZENDESK LEAD FINDER")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

        # Initialize components
        print("Initializing components...")

        try:
            # Initialize Google Sheets CRM
            self.crm = SheetsCRM(
                credentials_path=config.GOOGLE_SHEETS_CREDENTIALS_PATH,
                sheet_name=config.GOOGLE_SHEET_NAME,
                worksheet_name=config.WORKSHEET_NAME
            )

            # Initialize G2 scraper
            self.g2_scraper = G2Scraper(
                base_url=config.G2_ZENDESK_URL,
                request_delay=config.REQUEST_DELAY,
                use_cloudscraper=config.USE_CLOUDSCRAPER
            )

            # Initialize Zendesk showcase scraper
            self.zendesk_scraper = ZendeskShowcaseScraper(
                urls=config.ZENDESK_SHOWCASE_URLS,
                request_delay=config.REQUEST_DELAY,
                use_cloudscraper=config.USE_CLOUDSCRAPER
            )

            # Initialize enricher
            self.enricher = CompanyEnricher(
                enrichment_delay=config.ENRICHMENT_DELAY
            )

            print("\nAll components initialized successfully!")
            print(f"Current database size: {self.crm.get_company_count()} companies")
            print(f"Spreadsheet URL: {self.crm.get_spreadsheet_url()}\n")

        except Exception as e:
            print(f"\nERROR: Failed to initialize components: {str(e)}")
            print("\nPlease check:")
            print("  1. config.py is properly configured")
            print("  2. credentials.json exists and is valid")
            print("  3. Google Sheet is shared with service account")
            print("  4. All dependencies are installed")
            sys.exit(1)

    def run_full_pipeline(self, enable_enrichment=True):
        """
        Run the complete lead generation pipeline.

        Args:
            enable_enrichment (bool): Whether to enrich company data
        """
        print("\n" + "=" * 80)
        print("STARTING FULL PIPELINE")
        print("=" * 80 + "\n")

        all_companies = []

        # Step 1: Scrape G2
        print("\n" + "-" * 80)
        print("STEP 1: SCRAPING G2 REVIEWS")
        print("-" * 80)
        g2_companies = self.g2_scraper.scrape_multiple_pages(config.MAX_G2_PAGES)
        all_companies.extend(g2_companies)
        print(f"\nG2 Results: {len(g2_companies)} companies")

        # Step 2: Scrape Zendesk showcase
        print("\n" + "-" * 80)
        print("STEP 2: SCRAPING ZENDESK CUSTOMER SHOWCASE")
        print("-" * 80)
        zendesk_companies = self.zendesk_scraper.scrape_all_pages()
        all_companies.extend(zendesk_companies)
        print(f"\nZendesk Results: {len(zendesk_companies)} companies")

        # Step 3: Add known customers
        if config.USE_KNOWN_CUSTOMERS:
            print("\n" + "-" * 80)
            print("STEP 3: LOADING KNOWN CUSTOMERS")
            print("-" * 80)
            known_companies = get_known_customers()
            all_companies.extend(known_companies)
            print(f"\nKnown Customers: {len(known_companies)} companies")

        # Step 4: Deduplicate
        print("\n" + "-" * 80)
        print("STEP 4: DEDUPLICATION")
        print("-" * 80)
        print(f"Total companies before deduplication: {len(all_companies)}")
        all_companies = self._deduplicate_companies(all_companies)
        print(f"Unique companies after deduplication: {len(all_companies)}")

        # Step 5: Enrich
        if enable_enrichment and config.ENABLE_ENRICHMENT:
            print("\n" + "-" * 80)
            print("STEP 5: ENRICHING COMPANY DATA")
            print("-" * 80)
            all_companies = self.enricher.enrich_batch(all_companies)

            # Show enrichment stats
            stats = self.enricher.get_enrichment_stats(all_companies)
            print(f"\nEnrichment Statistics:")
            print(f"  Total companies: {stats['total']}")
            print(f"  With website: {stats['with_website']} ({stats['with_website']/stats['total']*100:.1f}%)")
            print(f"  With LinkedIn: {stats['with_linkedin']} ({stats['with_linkedin']/stats['total']*100:.1f}%)")
        else:
            print("\n" + "-" * 80)
            print("STEP 5: ENRICHMENT (SKIPPED)")
            print("-" * 80)

        # Step 6: Save to Google Sheets
        print("\n" + "-" * 80)
        print("STEP 6: SAVING TO GOOGLE SHEETS")
        print("-" * 80)
        save_stats = self.crm.add_companies_batch(all_companies, delay=0.5)

        # Final summary
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE!")
        print("=" * 80)
        print(f"\nFinal Statistics:")
        print(f"  Total companies found: {len(all_companies)}")
        print(f"  New companies added: {save_stats['added']}")
        print(f"  Duplicates skipped: {save_stats['duplicates']}")
        print(f"  Current database size: {self.crm.get_company_count()} companies")
        print(f"\nView your leads: {self.crm.get_spreadsheet_url()}")
        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def run_test(self):
        """
        Run a quick test of the pipeline with limited data.
        Does not save to Google Sheets.
        """
        print("\n" + "=" * 80)
        print("RUNNING TEST MODE")
        print("=" * 80 + "\n")

        all_companies = []

        # Test G2 scraping (1 page only)
        print("\n" + "-" * 80)
        print("TEST: G2 Scraping (1 page)")
        print("-" * 80)
        g2_companies = self.g2_scraper.scrape_reviews_page(1)
        all_companies.extend(g2_companies)
        print(f"\nFound {len(g2_companies)} companies from G2")

        # Test Zendesk scraping (first URL only)
        print("\n" + "-" * 80)
        print("TEST: Zendesk Showcase Scraping")
        print("-" * 80)
        zendesk_companies = self.zendesk_scraper.scrape_customer_page(config.ZENDESK_SHOWCASE_URLS[0])
        all_companies.extend(zendesk_companies)
        print(f"\nFound {len(zendesk_companies)} companies from Zendesk")

        # Add sample known customers
        print("\n" + "-" * 80)
        print("TEST: Known Customers (5 samples)")
        print("-" * 80)
        known_companies = get_known_customers()[:5]
        all_companies.extend(known_companies)
        print(f"\nLoaded {len(known_companies)} known customers")

        # Deduplicate
        print("\n" + "-" * 80)
        print("TEST: Deduplication")
        print("-" * 80)
        print(f"Before: {len(all_companies)} companies")
        all_companies = self._deduplicate_companies(all_companies)
        print(f"After: {len(all_companies)} unique companies")

        # Test enrichment (3 companies only)
        if all_companies:
            print("\n" + "-" * 80)
            print("TEST: Enrichment (3 companies)")
            print("-" * 80)
            sample_companies = all_companies[:3]
            enriched = self.enricher.enrich_batch(sample_companies)

            print("\n" + "-" * 80)
            print("SAMPLE ENRICHED DATA")
            print("-" * 80)
            for company in enriched:
                print(f"\nCompany: {company['name']}")
                print(f"  Website: {company.get('website', 'Not found')}")
                print(f"  LinkedIn: {company.get('linkedin_url', 'Not found')}")
                print(f"  Source: {company.get('source', 'Unknown')}")

        # Test complete
        print("\n" + "=" * 80)
        print("TEST COMPLETE!")
        print("=" * 80)
        print(f"\nTotal unique companies found: {len(all_companies)}")
        print("\nTest successful! Ready for full run.")
        print("Use: python main.py --mode full")
        print("=" * 80 + "\n")

    def run_g2_only(self, enable_enrichment=True):
        """
        Run only G2 scraping.

        Args:
            enable_enrichment (bool): Whether to enrich company data
        """
        print("\n" + "=" * 80)
        print("G2 SCRAPING ONLY")
        print("=" * 80 + "\n")

        # Scrape G2
        companies = self.g2_scraper.scrape_multiple_pages(config.MAX_G2_PAGES)

        # Enrich if enabled
        if enable_enrichment and config.ENABLE_ENRICHMENT:
            companies = self.enricher.enrich_batch(companies)

        # Save to sheets
        save_stats = self.crm.add_companies_batch(companies, delay=0.5)

        print(f"\nG2 scraping complete!")
        print(f"New companies added: {save_stats['added']}")
        print(f"View leads: {self.crm.get_spreadsheet_url()}\n")

    def run_zendesk_only(self, enable_enrichment=True):
        """
        Run only Zendesk showcase scraping.

        Args:
            enable_enrichment (bool): Whether to enrich company data
        """
        print("\n" + "=" * 80)
        print("ZENDESK SHOWCASE SCRAPING ONLY")
        print("=" * 80 + "\n")

        # Scrape Zendesk
        companies = self.zendesk_scraper.scrape_all_pages()

        # Enrich if enabled
        if enable_enrichment and config.ENABLE_ENRICHMENT:
            companies = self.enricher.enrich_batch(companies)

        # Save to sheets
        save_stats = self.crm.add_companies_batch(companies, delay=0.5)

        print(f"\nZendesk scraping complete!")
        print(f"New companies added: {save_stats['added']}")
        print(f"View leads: {self.crm.get_spreadsheet_url()}\n")

    def _deduplicate_companies(self, companies):
        """
        Remove duplicate companies from list.

        Args:
            companies (list): List of company dictionaries

        Returns:
            list: Deduplicated list of companies
        """
        if not config.ENABLE_DEDUPLICATION:
            return companies

        seen = set()
        unique_companies = []

        for company in companies:
            # Create a key for deduplication
            name_lower = company.get('name', '').lower().strip()

            if name_lower and name_lower not in seen:
                seen.add(name_lower)
                unique_companies.append(company)

        return unique_companies


def main():
    """
    Main entry point for the lead generation pipeline.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Zendesk Lead Finder - Automated Lead Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode full          # Run full pipeline
  python main.py --mode test          # Run test mode
  python main.py --mode g2-only       # Only scrape G2
  python main.py --no-enrich          # Skip enrichment
        """
    )

    parser.add_argument(
        '--mode',
        choices=['full', 'test', 'g2-only', 'zendesk-only'],
        default='full',
        help='Pipeline mode to run (default: full)'
    )

    parser.add_argument(
        '--no-enrich',
        action='store_true',
        help='Skip the enrichment step'
    )

    args = parser.parse_args()

    try:
        # Initialize pipeline
        pipeline = LeadGenPipeline()

        # Run selected mode
        if args.mode == 'test':
            pipeline.run_test()
        elif args.mode == 'g2-only':
            pipeline.run_g2_only(enable_enrichment=not args.no_enrich)
        elif args.mode == 'zendesk-only':
            pipeline.run_zendesk_only(enable_enrichment=not args.no_enrich)
        else:  # full mode
            pipeline.run_full_pipeline(enable_enrichment=not args.no_enrich)

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
