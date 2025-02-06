import logging
import os
from unittest.mock import Mock, patch

from dotenv import load_dotenv

from query_scanner import QueryScanner, QueryScannerException

# Load environment variables from .env file
load_dotenv()

# initialize constants defined in .env file
max_queries_per_scan = int(os.getenv("MAX_QUERIES_PER_SCAN", "10"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class  FailedValidationException(Exception):
    pass

class TestQueryScanner:
    def test_singleton_pattern(self):
        """Test that QueryScanner follows singleton pattern"""
        # Test that we get the same instance twice
        scanner1 = QueryScanner.get_singleton()
        scanner2 = QueryScanner.get_singleton()
        assert scanner1 is scanner2

        # Test that the instance is the singleton instance
        assert scanner1 is QueryScanner.get_singleton()

    def test_invalid_empty_queries(self):
        try:
            config = {"queries": [],"cron_string": "* * * * *"}
            scanner = QueryScanner.get_singleton()
            scanner.validate_config(config)
            raise FailedValidationException("validated config with empty queries")
        except QueryScannerException as error:
            assert error in "empty list of queries"

    def test_invalid_too_many_queries(self):
        try:
            queries = ["query1"] * (max_queries_per_scan + 1)
            config = { "cron_string": "* * * * *", "queries": queries }
            scanner = QueryScanner.get_singleton()
            scanner.validate_config(config)
            raise FailedValidationException("validated too many queries error")
        except QueryScannerException as error:
            assert error in "exceeded max queries"

    def test_invalid_cron_string(self):
        config = { "queries": ["query1"],"cron_string": "hello"}
        try:
            scanner = QueryScanner.get_singleton()
            scanner.validate_config(config)
            raise FailedValidationException("validated invalid cron-string valid")
        except QueryScannerException as error:
            assert error in "validated invalid cron-string"

    def test_valid_config(self):
        try:
            config = { "queries": ["query1"],"cron_string": "hello"}
            scanner = QueryScanner.get_singleton()
            scanner.validate_config(config)
        except QueryScannerException as exc:
            raise FailedValidationException("expected no exception") from exc

    @patch('query_scanner.QueryEngine')
    def test_run_queries(self, mock_query_engine):
        # Setup mock
        mock_search = Mock()
        mock_query_engine.return_value.search = mock_search

        # Define queries
        queries = ["Cowboys", "Indians"]

        # Run run_queries
        query_scanner = QueryScanner.get_singleton()
        query_scanner.run_queries(queries)

        # Verify search was called for each query
        assert mock_search.call_count == len(queries)
        mock_search.assert_any_call("Cowboys")
        mock_search.assert_any_call("Indians")

    @patch('query_scanner.schedule')
    @patch('query_scanner.croniter')
    def test_set_config(self, mock_schedule):
        query_scanner = QueryScanner.get_singleton()
        valid_config = { "queries":["fruits"], "chron_string": "* * * * *" }

        # Test configuration setting with mocked schedule
        with patch('query_scanner.time.sleep'):  # Prevent actual sleeping
            query_scanner.set_config(valid_config)
            assert query_scanner.run_status == "Running"
            # Verify schedule was set up
            assert mock_schedule.every.called

    def test_load_json_file_not_found(self):
        try:
            query_scanner = QueryScanner.get_singleton()
            query_scanner.load_json_file("nonexistent.json")
        except FileNotFoundError as error:
            assert error is not None
