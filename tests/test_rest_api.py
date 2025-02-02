from unittest.mock import patch, MagicMock
import pytest
from rest_api import RestApi
from youtube_query import YouTubeQuery

@pytest.fixture
def youtube_query_fixture():
    with patch('youtube_query.build') as mock_build, patch('youtube_query.YouTubeStorage') as mock_youtube_storage:
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_storage = mock_youtube_storage.return_value
        rest_api_instance = RestApi()
        yield rest_api_instance, mock_youtube, mock_storage

def test_search_success(fixture):
    rest_api_instance, mock_youtube, mock_storage = fixture
    mock_response = {
        "kind": "youtube#searchListResponse",
        "etag": "sWVvqWz_DYivV5xXaw8CkXsgiT4",
        "nextPageToken": "CAMQAA",
        "regionCode": "US",
        "pageInfo": {
            "totalResults": 1000000,
            "resultsPerPage": 3
        }
    }
    mock_youtube.search().list().execute.return_value = mock_response

    rest_api_instance.search('test_subject')

    mock_storage.get_response_row.assert_called_once()
    mock_storage.responses_table.insert_row.assert_called_once()
    mock_storage.responses_table.insert_rows.assert_called_once()

def test_search_http_error(fixture):
    rest_api_instance, mock_youtube, mock_storage = fixture
    mock_youtube.search().list().execute.side_effect = Exception("HTTP Error")

    rest_api_instance.search('test_subject')

    mock_storage.get_response_row.assert_not_called()
    mock_storage.responses_table.insert_row.assert_not_called()
    mock_storage.responses_table.insert_rows.assert_not_called()
