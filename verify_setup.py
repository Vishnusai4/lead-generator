#!/usr/bin/env python3
"""
Setup Verification Script for Zendesk Lead Finder

This script verifies that all prerequisites are met before running the pipeline:
- Python version
- Required packages
- Configuration file
- Credentials file
- Google Sheets connection

Usage:
    python verify_setup.py
"""

import sys
import os
import json


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_check(message, passed, details=""):
    """Print a check result."""
    status = "PASS" if passed else "FAIL"
    symbol = "" if passed else ""
    print(f"\n[{status}] {message}")
    if details:
        print(f"      {details}")


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print_header("CHECK 1: Python Version")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    required = (3, 8)
    passed = version >= required

    if passed:
        print_check(
            f"Python {version_str} detected",
            True,
            f"Required: Python {required[0]}.{required[1]}+"
        )
    else:
        print_check(
            f"Python {version_str} detected",
            False,
            f"Required: Python {required[0]}.{required[1]}+ | Please upgrade Python"
        )

    return passed


def check_dependencies():
    """Check if all required packages are installed."""
    print_header("CHECK 2: Required Packages")

    required_packages = {
        'requests': 'HTTP requests',
        'bs4': 'BeautifulSoup (HTML parsing)',
        'selenium': 'Browser automation',
        'gspread': 'Google Sheets API',
        'google.auth': 'Google authentication',
        'pandas': 'Data manipulation',
        'dotenv': 'Environment variables',
        'fake_useragent': 'Random user agents',
    }

    all_passed = True

    for package, description in required_packages.items():
        try:
            __import__(package)
            print_check(f"{package} - {description}", True)
        except ImportError:
            print_check(
                f"{package} - {description}",
                False,
                f"Install with: pip install {package}"
            )
            all_passed = False

    # Check optional packages
    print("\nOptional packages:")
    try:
        __import__('cloudscraper')
        print_check("cloudscraper (anti-bot bypassing)", True)
    except ImportError:
        print_check(
            "cloudscraper (anti-bot bypassing)",
            False,
            "Optional but recommended: pip install cloudscraper"
        )

    if not all_passed:
        print("\nTo install all dependencies:")
        print("  pip install -r requirements.txt")

    return all_passed


def check_config_file():
    """Check if config.py exists and is valid."""
    print_header("CHECK 3: Configuration File")

    config_path = "config.py"

    if not os.path.exists(config_path):
        print_check(
            "config.py file",
            False,
            "File not found | Create from template: cp config_template.py config.py"
        )
        return False

    # Try to import config
    try:
        import config

        # Check required attributes
        required_attrs = [
            'GOOGLE_SHEETS_CREDENTIALS_PATH',
            'GOOGLE_SHEET_NAME',
            'WORKSHEET_NAME',
            'G2_ZENDESK_URL',
            'ZENDESK_SHOWCASE_URLS'
        ]

        missing_attrs = []
        for attr in required_attrs:
            if not hasattr(config, attr):
                missing_attrs.append(attr)

        if missing_attrs:
            print_check(
                "config.py file",
                False,
                f"Missing attributes: {', '.join(missing_attrs)}"
            )
            return False

        print_check("config.py file exists and is valid", True)

        # Show current configuration
        print("\n      Current configuration:")
        print(f"        Credentials: {config.GOOGLE_SHEETS_CREDENTIALS_PATH}")
        print(f"        Sheet name: {config.GOOGLE_SHEET_NAME}")
        print(f"        Worksheet: {config.WORKSHEET_NAME}")

        return True

    except Exception as e:
        print_check(
            "config.py file",
            False,
            f"Error loading config: {str(e)}"
        )
        return False


def check_credentials():
    """Check if credentials.json exists and is valid."""
    print_header("CHECK 4: Google Cloud Credentials")

    # Import config to get credentials path
    try:
        import config
        creds_path = config.GOOGLE_SHEETS_CREDENTIALS_PATH
    except:
        print_check(
            "Reading credentials path from config",
            False,
            "Cannot read config.py"
        )
        return False

    # Check if credentials file exists
    if not os.path.exists(creds_path):
        print_check(
            f"Credentials file: {creds_path}",
            False,
            "File not found | Download from Google Cloud Console"
        )
        print("\n      How to get credentials:")
        print("        1. Go to console.cloud.google.com")
        print("        2. Create/select a project")
        print("        3. Enable Google Sheets API and Google Drive API")
        print("        4. Create Service Account")
        print("        5. Download JSON key")
        print(f"        6. Save as '{creds_path}'")
        return False

    # Try to load and validate JSON
    try:
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)

        # Check required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [f for f in required_fields if f not in creds_data]

        if missing_fields:
            print_check(
                f"Credentials file: {creds_path}",
                False,
                f"Invalid format | Missing fields: {', '.join(missing_fields)}"
            )
            return False

        if creds_data.get('type') != 'service_account':
            print_check(
                f"Credentials file: {creds_path}",
                False,
                "Must be a service account credential file"
            )
            return False

        print_check(f"Credentials file: {creds_path}", True)
        print(f"\n      Service account email: {creds_data['client_email']}")
        print("      Make sure to share your Google Sheet with this email!")

        return True

    except json.JSONDecodeError:
        print_check(
            f"Credentials file: {creds_path}",
            False,
            "Invalid JSON format"
        )
        return False
    except Exception as e:
        print_check(
            f"Credentials file: {creds_path}",
            False,
            f"Error reading file: {str(e)}"
        )
        return False


def check_google_sheets_connection():
    """Check if we can connect to Google Sheets."""
    print_header("CHECK 5: Google Sheets Connection")

    try:
        import config
        from sheets_crm import SheetsCRM

        print("      Attempting to connect to Google Sheets...")

        crm = SheetsCRM(
            credentials_path=config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            sheet_name=config.GOOGLE_SHEET_NAME,
            worksheet_name=config.WORKSHEET_NAME
        )

        # Try to get company count
        count = crm.get_company_count()

        print_check("Google Sheets connection", True)
        print(f"\n      Spreadsheet: {config.GOOGLE_SHEET_NAME}")
        print(f"      Worksheet: {config.WORKSHEET_NAME}")
        print(f"      Current companies: {count}")
        print(f"      URL: {crm.get_spreadsheet_url()}")

        return True

    except Exception as e:
        print_check(
            "Google Sheets connection",
            False,
            str(e)
        )
        print("\n      Common issues:")
        print("        1. Sheet not shared with service account email")
        print("        2. APIs not enabled (Sheets API, Drive API)")
        print("        3. Invalid credentials")
        print("        4. Network connection issues")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 80)
    print(" " * 20 + "SETUP VERIFICATION")
    print("=" * 80)
    print("\nThis script will verify your setup is correct.\n")

    results = []

    # Run all checks
    results.append(("Python Version", check_python_version()))
    results.append(("Required Packages", check_dependencies()))
    results.append(("Configuration File", check_config_file()))
    results.append(("Google Credentials", check_credentials()))
    results.append(("Google Sheets Connection", check_google_sheets_connection()))

    # Print summary
    print_header("VERIFICATION SUMMARY")

    all_passed = True
    for check_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)

    if all_passed:
        print("\nSUCCESS! All checks passed!")
        print("\nYou're ready to run the lead finder:")
        print("  python main.py --mode test       # Test run")
        print("  python main.py --mode full       # Full run")
        print("\n" + "=" * 80 + "\n")
        return 0
    else:
        print("\nSOME CHECKS FAILED!")
        print("\nPlease fix the issues above before running the lead finder.")
        print("Re-run this script after making changes: python verify_setup.py")
        print("\n" + "=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
