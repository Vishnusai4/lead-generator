"""
Comprehensive Test Suite for Zendesk Lead Generator

Tests:
- Detection module (with mocked HTTP)
- Enrichment module (with mocked APIs)
- Storage module (SQLite + CSV)
- Integration tests

Run with: pytest test_pipeline.py -v
"""

import os
import tempfile
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from detect_zendesk import ZendeskDetector
from enrichment import CompanyEnricher, ClearbitProvider, FreeProvider
from storage import LeadStorage


# Fixtures

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_csv():
    """Create temporary CSV for testing."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def storage(temp_db, temp_csv):
    """Initialize storage with temp files."""
    return LeadStorage(db_path=temp_db, csv_path=temp_csv)


# Test Storage Module

class TestStorage:
    """Test suite for storage.py"""

    def test_init_database(self, storage):
        """Test database initialization."""
        assert os.path.exists(storage.db_path)

    def test_save_lead(self, storage):
        """Test saving a lead."""
        lead_data = {
            'domain': 'test.com',
            'company_name': 'Test Company',
            'detected_zendesk': True,
            'zendesk_score': 100,
            'signals': {'script_zendesk': True},
            'blocked_by_waf': False,
            'detection_method': 'fast'
        }

        result = storage.save_lead(lead_data)
        assert result is True

        # Verify saved
        retrieved = storage.get_lead('test.com')
        assert retrieved is not None
        assert retrieved['domain'] == 'test.com'
        assert retrieved['detected_zendesk'] is True
        assert retrieved['zendesk_score'] == 100

    def test_lead_exists(self, storage):
        """Test lead existence check."""
        assert storage.lead_exists('test.com') is False

        storage.save_lead({'domain': 'test.com', 'detected_zendesk': False})
        assert storage.lead_exists('test.com') is True

    def test_update_lead(self, storage):
        """Test updating existing lead."""
        # Initial save
        storage.save_lead({
            'domain': 'test.com',
            'detected_zendesk': False,
            'zendesk_score': 0
        })

        # Update
        storage.save_lead({
            'domain': 'test.com',
            'detected_zendesk': True,
            'zendesk_score': 100
        })

        # Verify update
        lead = storage.get_lead('test.com')
        assert lead['detected_zendesk'] is True
        assert lead['zendesk_score'] == 100

    def test_get_all_leads(self, storage):
        """Test retrieving all leads."""
        # Add multiple leads
        storage.save_lead({'domain': 'test1.com', 'detected_zendesk': True, 'zendesk_score': 100})
        storage.save_lead({'domain': 'test2.com', 'detected_zendesk': False, 'zendesk_score': 0})
        storage.save_lead({'domain': 'test3.com', 'detected_zendesk': True, 'zendesk_score': 80})

        # Get all
        all_leads = storage.get_all_leads()
        assert len(all_leads) == 3

        # Get detected only
        detected = storage.get_all_leads(detected_only=True)
        assert len(detected) == 2

    def test_get_stats(self, storage):
        """Test statistics retrieval."""
        # Add test data
        storage.save_lead({'domain': 'test1.com', 'detected_zendesk': True, 'country': 'United States'})
        storage.save_lead({'domain': 'test2.com', 'detected_zendesk': False, 'blocked_by_waf': True})

        stats = storage.get_stats()
        assert stats['total_leads'] == 2
        assert stats['zendesk_detected'] == 1
        assert stats['blocked_by_waf'] == 1
        assert stats['us_companies'] == 1

    def test_export_to_csv(self, storage):
        """Test CSV export."""
        storage.save_lead({
            'domain': 'test.com',
            'company_name': 'Test Co',
            'detected_zendesk': True,
            'zendesk_score': 100
        })

        storage.export_to_csv()

        assert os.path.exists(storage.csv_path)
        assert os.path.getsize(storage.csv_path) > 0

    def test_batch_save(self, storage):
        """Test batch save operation."""
        leads = [
            {'domain': 'test1.com', 'detected_zendesk': True},
            {'domain': 'test2.com', 'detected_zendesk': False},
            {'domain': 'test3.com', 'detected_zendesk': True}
        ]

        stats = storage.batch_save(leads)
        assert stats['saved'] == 3
        assert stats['failed'] == 0


# Test Detection Module

class TestDetection:
    """Test suite for detect_zendesk.py"""

    @patch('detect_zendesk.requests.get')
    def test_fast_check_detected(self, mock_get):
        """Test fast detection with positive result."""
        # Mock successful response with Zendesk signals
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'''
            <html>
                <script src="https://static.zdassets.com/widget.js"></script>
                <a href="https://help.example.zendesk.com">Support</a>
            </html>
        '''
        mock_get.return_value = mock_response

        detector = ZendeskDetector()
        result = detector._fast_check('example.com')

        assert result['domain'] == 'example.com'
        assert result['detected'] is True
        assert result['score'] > 0
        assert 'cdn_zdassets' in result['signals']
        assert result['blocked_by_waf'] is False

    @patch('detect_zendesk.requests.get')
    def test_fast_check_blocked(self, mock_get):
        """Test detection with WAF blocking."""
        # Mock 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {'server': 'cloudflare'}
        mock_get.return_value = mock_response

        detector = ZendeskDetector()
        result = detector._fast_check('example.com')

        assert result['blocked_by_waf'] is True
        assert result['original_status_code'] == 403
        assert result['detected'] is False

    @patch('detect_zendesk.requests.get')
    def test_fast_check_not_detected(self, mock_get):
        """Test detection with no Zendesk signals."""
        # Mock response with no Zendesk
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'<html><body>Normal website</body></html>'
        mock_get.return_value = mock_response

        detector = ZendeskDetector()
        result = detector._fast_check('example.com')

        assert result['detected'] is False
        assert result['score'] == 0
        assert len(result['signals']) == 0

    def test_calculate_score(self):
        """Test signal score calculation."""
        detector = ZendeskDetector()

        signals = {
            'script_zendesk': True,
            'window_ze': True,
            'xhr_zendesk': True
        }

        score = detector._calculate_score(signals)
        assert score > 0
        assert score == detector.weights['script_zendesk'] + \
                       detector.weights['window_ze'] + \
                       detector.weights['xhr_zendesk']


# Test Enrichment Module

class TestEnrichment:
    """Test suite for enrichment.py"""

    @patch('enrichment.requests.get')
    def test_clearbit_success(self, mock_get):
        """Test successful Clearbit enrichment."""
        # Mock Clearbit API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'Example Company',
            'metrics': {'employees': 100},
            'category': {'industry': 'Software'},
            'geo': {
                'country': 'United States',
                'state': 'California',
                'city': 'San Francisco'
            },
            'linkedin': {'handle': 'example-company'}
        }
        mock_get.return_value = mock_response

        provider = ClearbitProvider(api_key='test_key')
        result = provider.enrich('example.com')

        assert result is not None
        assert result['company_name'] == 'Example Company'
        assert result['employees'] == 100
        assert result['country'] == 'United States'
        assert 'linkedin.com/company/example-company' in result['linkedin_url']

    @patch('enrichment.requests.get')
    def test_clearbit_not_found(self, mock_get):
        """Test Clearbit when domain not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        provider = ClearbitProvider(api_key='test_key')
        result = provider.enrich('example.com')

        assert result is None

    def test_free_provider_tld_inference(self):
        """Test free provider TLD-based country inference."""
        provider = FreeProvider()

        assert provider._get_country_from_tld('example.com') == 'United States'
        assert provider._get_country_from_tld('example.uk') == 'United Kingdom'
        assert provider._get_country_from_tld('example.de') == 'Germany'

    def test_free_provider_company_name_extraction(self):
        """Test company name extraction from domain."""
        provider = FreeProvider()

        assert provider._extract_company_name('shopify.com') == 'Shopify'
        assert provider._extract_company_name('my-company.com') == 'My Company'
        assert provider._extract_company_name('abc_corp.com') == 'Abc Corp'

    def test_enricher_us_filtering(self):
        """Test US-only filtering."""
        enricher = CompanyEnricher(us_only=True)

        # Mock provider that returns non-US company
        with patch.object(FreeProvider, 'enrich', return_value={
            'company_name': 'Test',
            'country': 'Canada',
            'enrichment_source': 'free'
        }):
            result = enricher.enrich('example.ca')
            assert result is None  # Should be filtered out

        # Mock provider that returns US company
        with patch.object(FreeProvider, 'enrich', return_value={
            'company_name': 'Test',
            'country': 'United States',
            'enrichment_source': 'free'
        }):
            result = enricher.enrich('example.com')
            assert result is not None
            assert result['country'] == 'United States'


# Integration Tests

class TestIntegration:
    """Integration tests for full pipeline."""

    @patch('detect_zendesk.requests.get')
    def test_full_pipeline(self, mock_get, storage):
        """Test complete detection + storage flow."""
        # Mock detection response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'<script src="https://static.zdassets.com/widget.js"></script>'
        mock_get.return_value = mock_response

        # Detect
        detector = ZendeskDetector()
        detection_result = detector._fast_check('example.com')

        # Prepare lead data
        lead_data = {
            'domain': 'example.com',
            'detected_zendesk': detection_result['detected'],
            'zendesk_score': detection_result['score'],
            'signals': detection_result['signals'],
            'blocked_by_waf': detection_result['blocked_by_waf']
        }

        # Save
        storage.save_lead(lead_data)

        # Verify
        saved = storage.get_lead('example.com')
        assert saved is not None
        assert saved['detected_zendesk'] is True
        assert saved['zendesk_score'] > 0


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
