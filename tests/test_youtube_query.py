# pylint: disable=all

import logging
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Importing from your module where YouTubeQuery is defined
from youtube_query import YouTubeQuery, HttpError

@pytest.fixture(autouse=True, scope="function")
def setup_logging():
    logging.basicConfig(level=logging.INFO)
    print("Logging setup executed")
    logging.debug("Logging setup for test")

@pytest.fixture
def mock_logger():
    mock_log = MagicMock()
    with patch('youtube_query.logger', mock_log):
        yield mock_log

@pytest.fixture
def mock_youtube():
    with patch('youtube_query.build') as mock_build:
        inner_mock_youtube = MagicMock()
        mock_build.return_value = inner_mock_youtube
        yield inner_mock_youtube

@pytest.fixture
def mock_storage():
    with patch('youtube_storage.YouTubeStorage.get_singleton') as mock_get_singleton:
        inner_mock_storage = MagicMock()
        mock_get_singleton.return_value = inner_mock_storage
        yield inner_mock_storage

@pytest.fixture
def query_instance(mock_youtube, mock_storage):
    return YouTubeQuery()

class TestYouTubeQuery:
    def test_search_success(self, query_instance, mock_youtube, mock_storage, mock_logger, caplog):
        mock_youtube.search().list().execute.return_value = {"items": [{"id": "video1"}]}
        query_instance.search("test_subject")
        mock_logger.info.assert_any_call("request submitted with params: part=snippet, q=test_subject, type=video, maxResults=25")
        mock_logger.info.assert_any_call("response received")
        mock_logger.info.assert_any_call("storing query response")
        mock_logger.info.assert_any_call("query response stored")

    def test_search_http_error(self, query_instance, mock_youtube, mock_storage, mock_logger):
        mock_http_error = HttpError(MagicMock(status=403), b'Error')
        mock_http_error.reason = 'Permission Denied'  # Mock this if you want a specific reason
        mock_youtube.search().list().execute.side_effect = mock_http_error
        query_instance.search("test_subject")
        mock_logger.error.assert_called_with(
            f"An HTTP error occurred: {mock_http_error}"
        )
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
