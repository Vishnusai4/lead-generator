"""
CSV-based CRM

Simple CRM that saves company data to a local CSV file.
No Google Cloud setup required - everything is stored locally.

Requirements:
- pandas library
- csv module (built-in)
"""

import csv
import os
import pandas as pd
from datetime import datetime


class CSVCRM:
    """
    A simple CRM class that uses CSV files as the database.
    Handles company data storage, deduplication, and updates.
    """

    # Column headers for the CRM
    HEADERS = [
        'Company Name',
        'Website',
        'Industry',
        'Company Size',
        'Location',
        'Description',
        'LinkedIn URL',
        'Uses Zendesk',
        'Source',
        'Date Added',
        'Status',
        'Notes',
        'Contact Found',
        'Contact Name',
        'Contact Email',
        'Contact LinkedIn',
        'Last Updated'
    ]

    def __init__(self, csv_file_path="leads.csv"):
        """
        Initialize the CSV CRM.

        Args:
            csv_file_path (str): Path to the CSV file
        """
        self.csv_file_path = csv_file_path
        self.df = None

        # Create or load the CSV file
        self._initialize()

    def _initialize(self):
        """
        Initialize the CSV file - create if doesn't exist, load if exists.
        """
        if os.path.exists(self.csv_file_path):
            # Load existing CSV
            try:
                self.df = pd.read_csv(self.csv_file_path)
                print(f"✅ Loaded existing database: {self.csv_file_path}")
                print(f"   Current companies: {len(self.df)}")
            except Exception as e:
                print(f"⚠️  Error loading CSV, creating new: {str(e)}")
                self._create_new_csv()
        else:
            # Create new CSV
            self._create_new_csv()

    def _create_new_csv(self):
        """
        Create a new CSV file with headers.
        """
        self.df = pd.DataFrame(columns=self.HEADERS)
        self.df.to_csv(self.csv_file_path, index=False)
        print(f"✅ Created new database: {self.csv_file_path}")

    def company_exists(self, company_name, website=None):
        """
        Check if a company already exists in the CRM.

        Args:
            company_name (str): Name of the company
            website (str, optional): Website URL for additional verification

        Returns:
            bool: True if company exists, False otherwise
        """
        # Normalize company name for comparison
        company_lower = company_name.lower().strip()

        # Check for exact match by name
        if 'Company Name' in self.df.columns:
            existing_names = self.df['Company Name'].str.lower().str.strip()
            if company_lower in existing_names.values:
                return True

        # If website provided, check for website match
        if website and 'Website' in self.df.columns:
            website_lower = website.lower().strip()
            existing_websites = self.df['Website'].str.lower().str.strip()
            if website_lower in existing_websites.values:
                return True

        return False

    def add_company(self, company_data):
        """
        Add a single company to the CRM.

        Args:
            company_data (dict): Dictionary containing company information

        Returns:
            bool: True if added successfully, False if duplicate or error
        """
        try:
            company_name = company_data.get('name', 'Unknown')
            website = company_data.get('website', '')

            # Check for duplicates
            if self.company_exists(company_name, website):
                print(f"  ⏭️  Skipping duplicate: {company_name}")
                return False

            # Prepare row data
            row_data = {
                'Company Name': company_data.get('name', ''),
                'Website': company_data.get('website', ''),
                'Industry': company_data.get('industry', ''),
                'Company Size': company_data.get('company_size', ''),
                'Location': company_data.get('location', ''),
                'Description': company_data.get('description', ''),
                'LinkedIn URL': company_data.get('linkedin_url', ''),
                'Uses Zendesk': 'Yes' if company_data.get('uses_zendesk', False) else 'Unknown',
                'Source': company_data.get('source', ''),
                'Date Added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'New',
                'Notes': '',
                'Contact Found': 'No',
                'Contact Name': '',
                'Contact Email': '',
                'Contact LinkedIn': '',
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Add to dataframe
            self.df = pd.concat([self.df, pd.DataFrame([row_data])], ignore_index=True)

            # Save to CSV
            self.df.to_csv(self.csv_file_path, index=False)

            print(f"  ✅ Added: {company_name}")
            return True

        except Exception as e:
            print(f"  ❌ Error adding company {company_data.get('name', 'Unknown')}: {str(e)}")
            return False

    def add_companies_batch(self, companies_list, delay=0.0):
        """
        Add multiple companies to the CRM in batch.

        Args:
            companies_list (list): List of company dictionaries
            delay (float): Delay between each add operation (not used for CSV)

        Returns:
            dict: Statistics about the batch operation
        """
        stats = {
            'total': len(companies_list),
            'added': 0,
            'duplicates': 0,
            'errors': 0
        }

        print(f"\n📊 Adding {len(companies_list)} companies to CSV database...")

        for i, company in enumerate(companies_list, 1):
            print(f"\n[{i}/{len(companies_list)}]", end=" ")

            success = self.add_company(company)

            if success:
                stats['added'] += 1
            elif self.company_exists(company.get('name', ''), company.get('website', '')):
                stats['duplicates'] += 1
            else:
                stats['errors'] += 1

        # Print summary
        print(f"\n\n{'='*60}")
        print(f"BATCH ADD SUMMARY")
        print(f"{'='*60}")
        print(f"Total processed:  {stats['total']}")
        print(f"✅ Added:         {stats['added']}")
        print(f"⏭️  Duplicates:    {stats['duplicates']}")
        print(f"❌ Errors:        {stats['errors']}")
        print(f"{'='*60}\n")

        return stats

    def get_all_companies(self):
        """
        Retrieve all companies from the CRM.

        Returns:
            list: List of dictionaries containing company data
        """
        return self.df.to_dict('records')

    def get_company_count(self):
        """
        Get the total number of companies in the CRM.

        Returns:
            int: Number of companies
        """
        return len(self.df)

    def update_company_status(self, company_name, status, notes=""):
        """
        Update the status and notes for a company.

        Args:
            company_name (str): Name of the company to update
            status (str): New status value
            notes (str): Additional notes

        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            company_lower = company_name.lower().strip()

            # Find the company
            mask = self.df['Company Name'].str.lower().str.strip() == company_lower

            if mask.any():
                # Update status and notes
                self.df.loc[mask, 'Status'] = status
                if notes:
                    self.df.loc[mask, 'Notes'] = notes
                self.df.loc[mask, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Save to CSV
                self.df.to_csv(self.csv_file_path, index=False)

                print(f"✅ Updated {company_name}: Status = {status}")
                return True
            else:
                print(f"⚠️  Company not found: {company_name}")
                return False

        except Exception as e:
            print(f"❌ Error updating company: {str(e)}")
            return False

    def get_csv_path(self):
        """
        Get the path to the CSV file.

        Returns:
            str: Path to CSV file
        """
        return os.path.abspath(self.csv_file_path)

    def export_to_excel(self, excel_path="leads.xlsx"):
        """
        Export the database to Excel format.

        Args:
            excel_path (str): Path for the Excel file

        Returns:
            str: Path to the Excel file
        """
        try:
            self.df.to_excel(excel_path, index=False)
            print(f"✅ Exported to Excel: {excel_path}")
            return os.path.abspath(excel_path)
        except Exception as e:
            print(f"❌ Error exporting to Excel: {str(e)}")
            return None


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("CSV CRM TEST")
    print("=" * 80)

    # Create test CRM
    crm = CSVCRM("test_leads.csv")

    # Test adding companies
    test_companies = [
        {'name': 'Shopify', 'website': 'shopify.com', 'source': 'Test'},
        {'name': 'Slack', 'website': 'slack.com', 'source': 'Test'},
        {'name': 'Airbnb', 'website': 'airbnb.com', 'source': 'Test'},
    ]

    print("\nAdding test companies...")
    for company in test_companies:
        crm.add_company(company)

    print(f"\n✅ Total companies in database: {crm.get_company_count()}")
    print(f"📁 CSV file location: {crm.get_csv_path()}")

    # Test duplicate detection
    print("\nTesting duplicate detection...")
    crm.add_company({'name': 'Shopify', 'website': 'shopify.com', 'source': 'Test'})

    print("\n" + "=" * 80)
