"""
Google Sheets CRM Integration

This module provides a simple CRM interface using Google Sheets as the backend.
It handles all interactions with Google Sheets for storing and managing company data.

Requirements:
- gspread library
- google-auth library
- Service account credentials JSON file
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time


class SheetsCRM:
    """
    A simple CRM class that uses Google Sheets as the database.
    Handles company data storage, deduplication, and updates.
    """

    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

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

    def __init__(self, credentials_path, sheet_name, worksheet_name="Companies"):
        """
        Initialize the SheetsCRM.

        Args:
            credentials_path (str): Path to Google service account credentials JSON
            sheet_name (str): Name of the Google Sheet
            worksheet_name (str): Name of the worksheet/tab (default: "Companies")
        """
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.worksheet_name = worksheet_name
        self.client = None
        self.spreadsheet = None
        self.worksheet = None

        # Connect to Google Sheets
        self._connect()

    def _connect(self):
        """
        Establish connection to Google Sheets using service account credentials.
        """
        try:
            # Authenticate with Google Sheets
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)

            # Open or create the spreadsheet
            try:
                self.spreadsheet = self.client.open(self.sheet_name)
                print(f" Connected to existing spreadsheet: {self.sheet_name}")
            except gspread.SpreadsheetNotFound:
                self.spreadsheet = self.client.create(self.sheet_name)
                print(f" Created new spreadsheet: {self.sheet_name}")

            # Open or create the worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                print(f" Connected to worksheet: {self.worksheet_name}")
            except gspread.WorksheetNotFound:
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=self.worksheet_name,
                    rows=1000,
                    cols=len(self.HEADERS)
                )
                print(f" Created new worksheet: {self.worksheet_name}")

            # Initialize headers if worksheet is empty
            if self.worksheet.row_count == 0 or not self.worksheet.row_values(1):
                self._initialize_headers()

        except FileNotFoundError:
            raise Exception(
                f"L Credentials file not found: {self.credentials_path}\n"
                "Please download your service account credentials from Google Cloud Console."
            )
        except Exception as e:
            raise Exception(f"L Failed to connect to Google Sheets: {str(e)}")

    def _initialize_headers(self):
        """
        Initialize the worksheet with column headers and formatting.
        """
        # Set headers in first row
        self.worksheet.update('A1', [self.HEADERS])

        # Format header row (blue background, white text, bold)
        self.worksheet.format('A1:Q1', {
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
            'textFormat': {
                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                'bold': True
            },
            'horizontalAlignment': 'CENTER'
        })

        # Freeze header row
        self.worksheet.freeze(rows=1)

        print(" Headers initialized and formatted")

    def company_exists(self, company_name, website=None):
        """
        Check if a company already exists in the CRM.

        Args:
            company_name (str): Name of the company
            website (str, optional): Website URL for additional verification

        Returns:
            bool: True if company exists, False otherwise
        """
        try:
            # Get all company names (column A, skipping header)
            company_names = self.worksheet.col_values(1)[1:]  # Skip header row

            # Normalize company name for comparison
            company_lower = company_name.lower().strip()

            # Check for exact match
            for existing_name in company_names:
                if existing_name.lower().strip() == company_lower:
                    return True

            # If website provided, check for website match
            if website:
                websites = self.worksheet.col_values(2)[1:]  # Column B
                website_lower = website.lower().strip()
                for existing_website in websites:
                    if existing_website.lower().strip() == website_lower:
                        return True

            return False

        except Exception as e:
            print(f"  Error checking if company exists: {str(e)}")
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
                print(f"    Skipping duplicate: {company_name}")
                return False

            # Prepare row data
            row_data = [
                company_data.get('name', ''),
                company_data.get('website', ''),
                company_data.get('industry', ''),
                company_data.get('company_size', ''),
                company_data.get('location', ''),
                company_data.get('description', ''),
                company_data.get('linkedin_url', ''),
                'Yes' if company_data.get('uses_zendesk', False) else 'Unknown',
                company_data.get('source', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'New',  # Status
                '',     # Notes
                'No',   # Contact Found
                '',     # Contact Name
                '',     # Contact Email
                '',     # Contact LinkedIn
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Last Updated
            ]

            # Add to sheet
            self.worksheet.append_row(row_data)
            print(f"   Added: {company_name}")
            return True

        except Exception as e:
            print(f"  L Error adding company {company_data.get('name', 'Unknown')}: {str(e)}")
            return False

    def add_companies_batch(self, companies_list, delay=0.5):
        """
        Add multiple companies to the CRM in batch.

        Args:
            companies_list (list): List of company dictionaries
            delay (float): Delay between each add operation (seconds)

        Returns:
            dict: Statistics about the batch operation
        """
        stats = {
            'total': len(companies_list),
            'added': 0,
            'duplicates': 0,
            'errors': 0
        }

        print(f"\n= Adding {len(companies_list)} companies to Google Sheets...")

        for i, company in enumerate(companies_list, 1):
            print(f"\n[{i}/{len(companies_list)}]", end=" ")

            success = self.add_company(company)

            if success:
                stats['added'] += 1
            elif self.company_exists(company.get('name', ''), company.get('website', '')):
                stats['duplicates'] += 1
            else:
                stats['errors'] += 1

            # Respect rate limits
            if delay > 0 and i < len(companies_list):
                time.sleep(delay)

        # Print summary
        print(f"\n\n{'='*60}")
        print(f"BATCH ADD SUMMARY")
        print(f"{'='*60}")
        print(f"Total processed:  {stats['total']}")
        print(f" Added:         {stats['added']}")
        print(f"  Duplicates:    {stats['duplicates']}")
        print(f"L Errors:        {stats['errors']}")
        print(f"{'='*60}\n")

        return stats

    def get_all_companies(self):
        """
        Retrieve all companies from the CRM.

        Returns:
            list: List of dictionaries containing company data
        """
        try:
            # Get all data from worksheet
            all_data = self.worksheet.get_all_records()
            return all_data

        except Exception as e:
            print(f"L Error retrieving companies: {str(e)}")
            return []

    def get_company_count(self):
        """
        Get the total number of companies in the CRM.

        Returns:
            int: Number of companies (excluding header row)
        """
        try:
            # Get row count and subtract 1 for header
            return max(0, self.worksheet.row_count - 1)

        except Exception as e:
            print(f"L Error getting company count: {str(e)}")
            return 0

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
            # Find the company row
            company_names = self.worksheet.col_values(1)
            company_lower = company_name.lower().strip()

            for i, name in enumerate(company_names[1:], start=2):  # Start from row 2
                if name.lower().strip() == company_lower:
                    # Update status (column K) and notes (column L)
                    self.worksheet.update_cell(i, 11, status)
                    if notes:
                        self.worksheet.update_cell(i, 12, notes)
                    # Update last modified (column Q)
                    self.worksheet.update_cell(i, 17, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                    print(f" Updated {company_name}: Status = {status}")
                    return True

            print(f"  Company not found: {company_name}")
            return False

        except Exception as e:
            print(f"L Error updating company: {str(e)}")
            return False

    def get_spreadsheet_url(self):
        """
        Get the URL of the Google Spreadsheet.

        Returns:
            str: URL to the spreadsheet
        """
        return self.spreadsheet.url if self.spreadsheet else ""

    def clear_all_data(self, keep_headers=True):
        """
        Clear all data from the worksheet.
        WARNING: This will delete all company data!

        Args:
            keep_headers (bool): If True, keep the header row

        Returns:
            bool: True if cleared successfully
        """
        try:
            if keep_headers:
                # Clear all rows except header
                self.worksheet.delete_rows(2, self.worksheet.row_count)
            else:
                # Clear everything
                self.worksheet.clear()

            print(" Worksheet cleared")
            return True

        except Exception as e:
            print(f"L Error clearing worksheet: {str(e)}")
            return False


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("GOOGLE SHEETS CRM TEST")
    print("=" * 80)
    print("\nThis module requires Google Sheets credentials to test.")
    print("To test manually, import this class and initialize with your credentials.")
    print("\nExample:")
    print("  from sheets_crm import SheetsCRM")
    print("  crm = SheetsCRM('credentials.json', 'My Sheet Name')")
    print("  crm.add_company({'name': 'Test Company', 'website': 'test.com'})")
    print("=" * 80)
