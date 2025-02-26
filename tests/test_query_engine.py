# pylint: disable=all

import os
import logging
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Importing from your module where QueryEngine is defined
from youtube.query_engine import QueryEngine, HttpError, QueryEngineException

@pytest.fixture(autouse=True, scope="function")
def setup_logging():
    logging.basicConfig(level=logging.INFO)
    print("Logging setup executed")
    logging.debug("Logging setup for test")

@pytest.fixture
def mock_logger():
    mock_log = MagicMock()
    with patch('youtube.query_engine.logger', mock_log):
        yield mock_log

@pytest.fixture
def mock_engine():
    with patch('youtube.query_engine.build') as mock_build:
        inner_mock_engine = MagicMock()
        mock_build.return_value = inner_mock_engine
        yield inner_mock_engine

@pytest.fixture
def mock_storage():
    with patch('youtube.youtube_storage.YouTubeStorage.get_singleton') as mock_get_singleton:
        inner_mock_storage = MagicMock()
        mock_get_singleton.return_value = inner_mock_storage
        yield inner_mock_storage

@pytest.fixture
def query_instance(mock_engine, mock_storage):
    return QueryEngine()

class TestQueryEngine:
    def test_singleton(self):
        query_engine1 = QueryEngine()
        query_engine2 = QueryEngine()
        assert query_engine1 is query_engine2

    def test_singleton_pattern(self):
        query_engine1 = QueryEngine.get_singleton()
        query_engine2 = QueryEngine.get_singleton()
        assert query_engine1 is query_engine2

    def test_search_success(self, query_instance, mock_engine, mock_storage, mock_logger, caplog):
        mock_engine.search().list().execute.return_value = {"items": [{"id": "video1"}]}
        query_instance.search("test_subject")
        mock_logger.info.assert_any_call("request submitted with params: part=snippet, q=test_subject, type=video, maxResults=25")
        mock_logger.info.assert_any_call("response received")
        mock_logger.info.assert_any_call("storing query request and response")

    def test_search_http_error(self, query_instance, mock_engine, mock_storage, mock_logger, caplog):
        mock_http_error = HttpError(MagicMock(status=403), b'Error')
        mock_http_error.reason = 'Permission Denied'  # Mock this if you want a specific reason
        mock_engine.search().list().execute.side_effect = mock_http_error

        try:
            query_instance.search("test_subject")
        except QueryEngineException:
            print("Caught QueryEngineException as expected")
            pass

        # Print the actual calls made to mock_logger.error
        print("***",mock_logger.error.call_args_list,"***")
        for call in mock_logger.error.call_args_list:
            print(call)

    def test_stringify_params_format(self, query_instance):
        params = {"part": "snippet", "q": "test", "type": "video", "maxResults": 25}
        result = query_instance.stringify_params(**params)
        assert result == "part=snippet, q=test, type=video, maxResults=25"

    def test_basic_logging(self, caplog):
        import logging
        caplog.set_level(logging.DEBUG)
        print(f"Current logging handlers: {logging.getLogger().handlers}")
        logging.info("Basic log test")
        print(f"caplog.text: |{caplog.text}|")
        assert "Basic log test" in caplog.text
        def test_search_no_api_key(self, mock_engine, mock_storage, mock_logger):
            with patch.dict(os.environ, {"YOUTUBE_API_KEY": ""}):
                with pytest.raises(RuntimeError, match="QueryEngine YOUTUBE_API_KEY is undefined"):
                    QueryEngine()
    
    def test_undefined_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="QueryEngine YOUTUBE_API_KEY is undefined"):
                QueryEngine() 
            assert QueryEngine._instance is None
            assert "QueryEngine YOUTUBE_API_KEY is undefined" in str(RuntimeError.args)

    def test_search_invalid_api_key(self, query_instance, mock_engine, mock_storage, mock_logger):
        mock_http_error = HttpError(MagicMock(status=400), b'Error')
        mock_http_error.reason = 'Bad Request'
        mock_engine.search().list().execute.side_effect = mock_http_error

        with pytest.raises(QueryEngineException):
            query_instance.search("invalid_key_test")

        mock_logger.error.assert_called_with(
            f"An HTTP error occurred: {mock_http_error}"
        )

    def test_search_no_results(self, query_instance, mock_engine, mock_storage, mock_logger):
        mock_engine.search().list().execute.return_value = {"items": []}
        query_instance.search("no_results_test")
        mock_logger.info.assert_any_call("request submitted with params: part=snippet, q=no_results_test, type=video, maxResults=25")
        mock_logger.info.assert_any_call("response received")
        mock_logger.info.assert_any_call("storing query request and response")
        mock_storage.add_query_request_and_response.assert_called_once()

        def test_search_no_api_key(self, mock_engine, mock_storage, mock_logger):
            with patch.dict(os.environ, {"YOUTUBE_API_KEY": ""}):
                with pytest.raises(RuntimeError, match="QueryEngine YOUTUBE_API_KEY is undefined"):
                    QueryEngine()

            def test_search_invalid_api_key(self, query_instance, mock_engine, mock_storage, mock_logger):
                mock_http_error = HttpError(MagicMock(status=400), b'Error')
                mock_http_error.reason = 'Bad Request'
                mock_engine.search().list().execute.side_effect = mock_http_error

                with pytest.raises(QueryEngineException):
                    query_instance.search("invalid_key_test")

                mock_logger.error.assert_called_with(
                    f"An HTTP error occurred: {mock_http_error}"
                )

            def test_search_no_results(self, query_instance, mock_engine, mock_storage, mock_logger):
                mock_engine.search().list().execute.return_value = {"items": []}
                query_instance.search("no_results_test")
                mock_logger.info.assert_any_call("request submitted with params: part=snippet, q=no_results_test, type=video, maxResults=25")
                mock_logger.info.assert_any_call("response received")
                mock_logger.info.assert_any_call("storing query request and response")
                mock_storage.add_query_request_and_response.assert_called_once()