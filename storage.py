"""
Storage Layer for Zendesk Lead Pipeline

Handles persistence to both SQLite and CSV with automatic synchronization.
Supports all detection metadata including bot-blocking signals.
"""

import sqlite3
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LeadStorage:
    """
    Dual-persistence storage for lead data.

    Features:
    - SQLite database for structured queries
    - CSV export for easy sharing
    - Automatic deduplication
    - Bot-blocking metadata tracking
    - JSON serialization for signals
    """

    # Schema definition
    COLUMNS = [
        'company_name',
        'domain',
        'detected_zendesk',
        'zendesk_score',
        'signals',
        'employees',
        'industry',
        'country',
        'state',
        'city',
        'linkedin_url',
        'enriched_at',
        'detection_timestamp',
        'blocked_by_waf',
        'original_status_code',
        'original_headers',
        'detection_method',
        'error'
    ]

    def __init__(self, db_path: str = 'leads.db', csv_path: str = 'leads.csv'):
        """
        Initialize storage with SQLite and CSV paths.

        Args:
            db_path: Path to SQLite database
            csv_path: Path to CSV export file
        """
        self.db_path = db_path
        self.csv_path = csv_path

        # Initialize database
        self._init_database()

        logger.info(f"Storage initialized: db={db_path}, csv={csv_path}")

    def _init_database(self):
        """Create database schema if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                domain TEXT UNIQUE NOT NULL,
                detected_zendesk BOOLEAN,
                zendesk_score INTEGER,
                signals TEXT,
                employees INTEGER,
                industry TEXT,
                country TEXT,
                state TEXT,
                city TEXT,
                linkedin_url TEXT,
                enriched_at TEXT,
                detection_timestamp TEXT,
                blocked_by_waf BOOLEAN,
                original_status_code INTEGER,
                original_headers TEXT,
                detection_method TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON leads(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected ON leads(detected_zendesk)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON leads(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocked ON leads(blocked_by_waf)')

        conn.commit()
        conn.close()

        logger.info("Database schema initialized")

    def save_lead(self, lead_data: Dict) -> bool:
        """
        Save or update a lead record.

        Args:
            lead_data: Dictionary with lead information

        Returns:
            bool: True if saved/updated, False if failed
        """
        try:
            domain = lead_data.get('domain')
            if not domain:
                logger.error("Cannot save lead without domain")
                return False

            # Prepare data for database
            db_data = self._prepare_for_db(lead_data)

            # Check if lead exists
            if self.lead_exists(domain):
                return self._update_lead(domain, db_data)
            else:
                return self._insert_lead(db_data)

        except Exception as e:
            logger.error(f"Failed to save lead {lead_data.get('domain')}: {str(e)}")
            return False

    def _insert_lead(self, db_data: Dict) -> bool:
        """Insert new lead into database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            columns = ', '.join(db_data.keys())
            placeholders = ', '.join(['?' for _ in db_data])
            values = tuple(db_data.values())

            cursor.execute(f'''
                INSERT INTO leads ({columns})
                VALUES ({placeholders})
            ''', values)

            conn.commit()
            logger.info(f"Inserted new lead: {db_data.get('domain')}")
            return True

        except sqlite3.IntegrityError as e:
            logger.warning(f"Lead already exists: {db_data.get('domain')}")
            return False
        finally:
            conn.close()

    def _update_lead(self, domain: str, db_data: Dict) -> bool:
        """Update existing lead in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Remove domain from update data
            update_data = {k: v for k, v in db_data.items() if k != 'domain'}
            update_data['updated_at'] = datetime.utcnow().isoformat()

            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            values = tuple(update_data.values()) + (domain,)

            cursor.execute(f'''
                UPDATE leads
                SET {set_clause}
                WHERE domain = ?
            ''', values)

            conn.commit()
            logger.info(f"Updated lead: {domain}")
            return True

        finally:
            conn.close()

    def _prepare_for_db(self, lead_data: Dict) -> Dict:
        """
        Prepare lead data for database insertion.

        Converts complex types to strings, handles missing fields.
        """
        db_data = {}

        # Map all known fields
        for column in self.COLUMNS:
            value = lead_data.get(column)

            # Convert signals dict to JSON string
            if column == 'signals' and isinstance(value, dict):
                db_data[column] = json.dumps(value)

            # Convert boolean to int for SQLite
            elif column in ['detected_zendesk', 'blocked_by_waf']:
                db_data[column] = 1 if value else 0

            # Keep other values as-is
            else:
                db_data[column] = value

        return db_data

    def lead_exists(self, domain: str) -> bool:
        """Check if lead already exists in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM leads WHERE domain = ?', (domain,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists

    def get_processed_domains(self) -> set:
        """
        Get set of all domains that have already been processed.

        Returns:
            set: Set of domain strings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT domain FROM leads')
            domains = {row[0] for row in cursor.fetchall()}
            return domains
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return set()
        finally:
            conn.close()

    def get_lead(self, domain: str) -> Optional[Dict]:
        """
        Retrieve a lead by domain.

        Args:
            domain: Company domain

        Returns:
            dict: Lead data or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM leads WHERE domain = ?', (domain,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def get_all_leads(self, detected_only: bool = False,
                      us_only: bool = False) -> List[Dict]:
        """
        Retrieve all leads with optional filtering.

        Args:
            detected_only: Only return Zendesk-detected leads
            us_only: Only return US-based companies

        Returns:
            list: List of lead dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM leads WHERE 1=1'
        params = []

        if detected_only:
            query += ' AND detected_zendesk = 1'

        if us_only:
            query += ' AND country = ?'
            params.append('United States')

        query += ' ORDER BY zendesk_score DESC, company_name'

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        return [self._row_to_dict(row) for row in rows]

    def get_blocked_leads(self) -> List[Dict]:
        """Get all leads that were blocked by WAF."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM leads WHERE blocked_by_waf = 1')
        rows = cursor.fetchall()

        conn.close()

        return [self._row_to_dict(row) for row in rows]

    def get_stats(self) -> Dict:
        """
        Get database statistics.

        Returns:
            dict: Statistics about stored leads
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total leads
        cursor.execute('SELECT COUNT(*) FROM leads')
        stats['total_leads'] = cursor.fetchone()[0]

        # Detected Zendesk
        cursor.execute('SELECT COUNT(*) FROM leads WHERE detected_zendesk = 1')
        stats['zendesk_detected'] = cursor.fetchone()[0]

        # Blocked by WAF
        cursor.execute('SELECT COUNT(*) FROM leads WHERE blocked_by_waf = 1')
        stats['blocked_by_waf'] = cursor.fetchone()[0]

        # US companies
        cursor.execute('SELECT COUNT(*) FROM leads WHERE country = ?', ('United States',))
        stats['us_companies'] = cursor.fetchone()[0]

        # Enriched
        cursor.execute('SELECT COUNT(*) FROM leads WHERE enriched_at IS NOT NULL')
        stats['enriched'] = cursor.fetchone()[0]

        # Detection methods
        cursor.execute('SELECT detection_method, COUNT(*) FROM leads GROUP BY detection_method')
        stats['methods'] = dict(cursor.fetchall())

        conn.close()

        return stats

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite row to dictionary with proper types."""
        data = dict(row)

        # Convert signals JSON string back to dict
        if data.get('signals'):
            try:
                data['signals'] = json.loads(data['signals'])
            except json.JSONDecodeError:
                data['signals'] = {}

        # Convert boolean integers back to bool
        data['detected_zendesk'] = bool(data.get('detected_zendesk'))
        data['blocked_by_waf'] = bool(data.get('blocked_by_waf'))

        return data

    def export_to_csv(self, csv_path: Optional[str] = None,
                      detected_only: bool = False,
                      us_only: bool = False):
        """
        Export database to CSV.

        Args:
            csv_path: Optional custom CSV path (uses default if not provided)
            detected_only: Only export Zendesk-detected leads
            us_only: Only export US companies
        """
        csv_file = csv_path or self.csv_path
        leads = self.get_all_leads(detected_only=detected_only, us_only=us_only)

        if not leads:
            logger.warning("No leads to export")
            return

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            # Use all columns plus timestamps
            fieldnames = self.COLUMNS + ['created_at', 'updated_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')

            writer.writeheader()

            for lead in leads:
                # Convert signals dict to JSON string for CSV
                row = lead.copy()
                if isinstance(row.get('signals'), dict):
                    row['signals'] = json.dumps(row['signals'])

                writer.writerow(row)

        logger.info(f"Exported {len(leads)} leads to {csv_file}")

    def import_from_csv(self, csv_path: str):
        """
        Import leads from CSV file.

        Args:
            csv_path: Path to CSV file
        """
        imported = 0
        skipped = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Convert string booleans
                if 'detected_zendesk' in row:
                    row['detected_zendesk'] = row['detected_zendesk'].lower() in ['true', '1', 'yes']
                if 'blocked_by_waf' in row:
                    row['blocked_by_waf'] = row['blocked_by_waf'].lower() in ['true', '1', 'yes']

                # Convert signals JSON string to dict
                if 'signals' in row and row['signals']:
                    try:
                        row['signals'] = json.loads(row['signals'])
                    except json.JSONDecodeError:
                        row['signals'] = {}

                # Save lead
                if self.save_lead(row):
                    imported += 1
                else:
                    skipped += 1

        logger.info(f"Imported {imported} leads, skipped {skipped} duplicates from {csv_path}")

    def batch_save(self, leads: List[Dict]) -> Dict:
        """
        Save multiple leads in batch.

        Args:
            leads: List of lead dictionaries

        Returns:
            dict: Statistics about the batch operation
        """
        saved = 0
        updated = 0
        failed = 0

        for lead in leads:
            try:
                if self.lead_exists(lead.get('domain')):
                    if self.save_lead(lead):
                        updated += 1
                    else:
                        failed += 1
                else:
                    if self.save_lead(lead):
                        saved += 1
                    else:
                        failed += 1
            except Exception as e:
                logger.error(f"Failed to save lead in batch: {str(e)}")
                failed += 1

        stats = {
            'saved': saved,
            'updated': updated,
            'failed': failed,
            'total': len(leads)
        }

        logger.info(f"Batch save complete: {stats}")

        # Auto-export to CSV after batch
        self.export_to_csv()

        return stats

    def clear_database(self):
        """
        Clear all leads from database.

        WARNING: This is destructive and cannot be undone.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM leads')
        conn.commit()

        count = cursor.rowcount
        conn.close()

        logger.warning(f"Cleared {count} leads from database")
