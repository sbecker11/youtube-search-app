import unittest
from unittest.mock import patch, MagicMock
from youtube_query import YouTubeQuery

class TestYouTubeQuery(unittest.TestCase):

    @patch('youtube_query.build')
    @patch('youtube_query.YouTubeStorage')
    def setUp(self):
        self.mock_youtube = MagicMock()
        self.mock_build.return_value = YouTubeQuery()
        self.mock_storage = MagicMock()
        self.youtube_query = YouTubeQuery()

    def test_search_success(self):
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
        self.mock.mock_youtube_storage.return_value = TestYouTubStorage
        self.mock.mock_build.return_value = TestYouTubeQuery
        self.mock_youtube.search().list().execute.return_value = mock_response

        self.youtube_query.search('test_subject')

        self.mock_storage.get_response_row.assert_called_once()
        self.mock_storage.responses_table.insert_row.assert_called_once()
        self.mock_storage.responses_table.insert_rows.assert_called_once()

    def test_search_http_error(self):
        self.mock_youtube.search().list().execute.side_effect = Exception("HTTP Error")

        self.youtube_query.search('test_subject')

        self.mock_storage.get_response_row.assert_not_called()
        self.mock_storage.responses_table.insert_row.assert_not_called()
        self.mock_storage.responses_table.insert_rows.assert_not_called()

if __name__ == '__main__':
    unittest.main()
