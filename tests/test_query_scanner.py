import logging
import os
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

from query_scanner import QueryScanner, QueryScannerException

# Load environment variables from .env file
load_dotenv()

# initialize constants defined in .env file
max_queries_per_scan = int(os.getenv("MAX_QUERIES_PER_SCAN", "10"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def internal_valid_config():
    return {
        "queries": ["Cowboys", "Indians"],
        "cron_string": "* * * * *"
    }

@pytest.fixture
def internal_scanner(internal_valid_config):
    # Provide dependencies through the constructor
    return QueryScanner(config=internal_valid_config, query_engine=Mock())

class TestQueryScanner:
    def test_singleton_pattern(self):
        """Test that QueryScanner follows singleton pattern"""
        # Test that we get the same instance twice
        scanner1 = QueryScanner.get_singleton()
        scanner2 = QueryScanner.get_singleton()
        assert scanner1 is scanner2

        # Test that the instance is the singleton instance
        assert scanner1 is QueryScanner.get_singleton()

    def test_validate_empty_queries(self, internal_scanner):
        """Test validation of empty queries list"""
        invalid_config = {
            "queries": [],
            "cron_string": "* * * * *"
        }
        with pytest.raises(QueryScannerException) as exc:
            internal_scanner.validate_config(invalid_config)
        assert "empty list of queries" in str(exc.value)

    def test_config_too_many_queries(self, internal_scanner):
        """Test validation of too many queries"""
        too_many_queries = max_queries_per_scan + 1
        invalid_config = {
            "queries": ["query" + str(i) for i in range(too_many_queries)],
            "cron_string": "* * * * *"
        }
        with pytest.raises(QueryScannerException) as exc:
            internal_scanner.validate_config(invalid_config)
        assert "number of listed queries exceeds max_queries" in str(exc.value)

    def test_validate_invalid_cron(self, internal_scanner):
        """Test validation of invalid cron string"""
        invalid_config = {
            "queries": ["Cowboys"],
            "cron_string": "invalid cron"
        }
        with pytest.raises(QueryScannerException) as exc:
            internal_scanner.validate_config(invalid_config)
        assert "cron_string does not match the required pattern" in str(exc.value)

    @patch('query_scanner.QueryEngine')
    def test_run_queries(self, mock_query_engine, internal_scanner):
        """Test that queries are run correctly"""
        # Setup mock
        mock_search = Mock()
        mock_query_engine.return_value.search = mock_search

        # Define queries
        queries = ["Cowboys", "Indians"]

        # Run run_queries
        internal_scanner.run_queries(queries)

        # Verify search was called for each query
        assert mock_search.call_count == len(queries)
        mock_search.assert_any_call("Cowboys")
        mock_search.assert_any_call("Indians")

    @patch('query_scanner.schedule')
    @patch('query_scanner.croniter')
    def test_set_config(self, mock_schedule, internal_scanner, internal_valid_config):
        """Test configuration setting with mocked schedule"""
        with patch('query_scanner.time.sleep'):  # Prevent actual sleeping
            internal_scanner.set_config(internal_valid_config)
            assert internal_scanner.run_status == "Running"
            # Verify schedule was set up
            assert mock_schedule.every.called

    def test_load_json_file_not_found(self, internal_scanner):
        """Test handling of non-existent config file"""
        result = internal_scanner.load_json_file("nonexistent.json")
        assert result is None
