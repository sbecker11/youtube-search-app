
import logging
import os
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv

from youtube_query_scanner import (YouTubeQueryScanner,
                                   YouTubeQueryScannerException)

# Load environment variables from .env file
load_dotenv()

# initialize constansts defined in .env file
max_queries_per_scan = int(os.getenv("MAX_QUERIES_PER_SCAN", "10"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def valid_config():
    return {
        "queries": ["Cowboys", "Indians"],
        "cron_string": "* * * * *"
    }

@pytest.fixture
def scanner():
    return YouTubeQueryScanner.get_singleton()

class TestYouTubeQueryScanner:
    def test_singleton_pattern(self):
        """Test that YouTubeQueryScanner follows singleton pattern"""
        # Test that we get the same instance twice
        scanner1 = YouTubeQueryScanner.get_singleton()
        scanner2 = YouTubeQueryScanner.get_singleton()
        assert scanner1 is scanner2

        # Test that the instance is the singleton instance
        assert scanner1 is YouTubeQueryScanner.get_singleton()

    def test_validate_empty_queries(self, scanner_instance):
        """Test validation of empty queries list"""
        invalid_config = {
            "queries": [],
            "cron_string": "* * * * *"
        }
        with pytest.raises(YouTubeQueryScannerException) as exc:
            scanner_instance.validate_config(invalid_config)
        assert "empty list of queries" in str(exc.value)

    def test_config_too_many_queries(self, scanner_fixture):
        """Test validation of too many queries"""
        too_many_queries = max_queries_per_scan + 1
        invalid_config = {
            "queries": ["query" + str(i) for i in range(too_many_queries)],
            "cron_string": "* * * * *"
        }
        with pytest.raises(YouTubeQueryScannerException) as exc:
            scanner_fixture.validate_config(invalid_config)
        assert "number of listed queries exceeds max_queries" in str(exc.value)

    def test_validate_invalid_cron(self, scanner_fixture):
        """Test validation of invalid cron string"""
        invalid_config = {
            "queries": ["Cowboys"],
            "cron_string": "invalid cron"
        }
        with pytest.raises(YouTubeQueryScannerException) as exc:
            scanner_fixture.validate_config(invalid_config)
        assert "cron_string does not match the required pattern" in str(exc.value)

    @patch('youtube_query_scanner.YouTubeQuery')
    def test_query_queries(self, mock_youtube_query, scanner_fixture, valid_config_param):
        """Test that queries are queried correctly"""
        # Setup mock
        mock_search = Mock()
        mock_youtube_query.return_value.search = mock_search

        # Run query_queries
        scanner_fixture.query_queries(valid_config_param["queries"])

        # Verify search was called for each query
        assert mock_search.call_count == len(valid_config["queries"])
        mock_search.assert_any_call("Cowboys")
        mock_search.assert_any_call("Indians")

    @patch('youtube_query_scanner.schedule')
    @patch('youtube_query_scanner.croniter')
    def test_set_config(self, mock_schedule, scanner_fixture):
        """Test configuration setting with mocked schedule"""
        with patch('youtube_query_scanner.time.sleep'):  # Prevent actual sleeping
            scanner_fixture.set_config(valid_config)
            assert scanner_fixture.run_status == "Running"
            # Verify schedule was set up
            assert mock_schedule.every.called

    def test_load_json_file_not_found(self, scanner_fixture):
        """Test handling of non-existent config file"""
        result = scanner_fixture.load_json_file("nonexistent.json")
        assert result is None
