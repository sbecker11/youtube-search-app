from unittest.mock import patch, MagicMock
import pytest
from rest_api import RestApi
from youtube_storage import YouTubeStorage

@pytest.fixture
def youtube_storage():
    with patch('youtube_storage.YouTubeTable') as mockTubeTable:
        mock_storage = MagicMock()
        mockTubeTable.return_value = mock_storage
        youtube_storage_instance = YouTubeStorage('Responses', 'Snippets')
        rest_api_instance = RestApi(youtube_storage_instance)
        yield rest_api_instance, mock_storage

def test_search_success(youtube_storage):
    rest_api_instance, mock_storage = youtube_storage
    mock_response = {
        "kind": "youtube#searchListResponse",
        "etag": "sWVvqWz_DYivV5xXsgiT4",
        "nextPageToken": "CAMQAA",
        "regionCode": "US",
        "pageInfo": {
            "totalResults": 1000000,
            "resultsPerPage": 3
        }
    }
    mock_storage.responses_table.execute_query.return_value = [mock_response]

    rest_api_instance.search('test_subject')

    mock_storage.get_response_row.assert_called_once()
    mock_storage.responses_table.insert_row.assert_called_once()
    mock_storage.responses_table.insert_rows.assert_called_once()

def test_search_http_error(youtube_storage):
    rest_api_instance, mock_storage = youtube_storage
    mock_storage.responses_table.execute_query.side_effect = Exception("HTTP Error")

    rest_api_instance.search('test_subject')

    mock_storage.get_response_row.assert_not_called()
    mock_storage.responses_table.insert_row.assert_not_called()
    mock_storage.responses_table.insert_rows.assert_not_called()
