from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_storage import YouTubeStorage

class YouTubeQuery:
    """Submits queries to YouTube metadata API
        and stores each query request and its
        query response details to YouTubeStorage.
    """
    def __init__(self,
                 youtube_api_key,
                 responses_table_name=None,
                 snippets_table_name=None,
                 config_url=None,
                 endpoint_url=None):
        """
        Args:
            youtube_api_key (str): youtube developer API key
            responses_table_name (str, optional): table used to store query requests and responses. Defaults to None.
            snippets_table_name (str, optional): used to store query result snippets. Defaults to None.
            config_url (str, optional): . url used to retrieve table configurations. Defaults to None.
            endpoint_url (str, optional): url used to submit queries. Defaults to None.
        """
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        self.youtube_storage = YouTubeStorage(responses_table_name, snippets_table_name, config_url, endpoint_url)

    def search(self, subject: str):
        request_params = {
            "part": "snippet",
            "q": subject,
            "type": "video",
            "maxResults": 25
        }
        try:
            request = self.youtube.search().list(**request_params)
            response = request.execute()
        except HttpError as error:
            print(f"An HTTP error occurred: {error}")
            return

        youtube_query = {
            'subject': subject,
            'requestSubmittedAt': datetime.utcnow().isoformat(),
            **request_params
        }
        response_row = self.youtube_storage.get_response_row(response, youtube_query)
        response_row.update({
            'kind': response.get('kind'),
            'etag': response.get('etag'),
            'nextPageToken': response.get('nextPageToken'),
            'regionCode': response.get('regionCode'),
            'totalResults': response['pageInfo'].get('totalResults'),
            'resultsPerPage': response['pageInfo'].get('resultsPerPage')
        })
        self.youtube_storage.responses_table.insert_row(response_row)
        self.youtube_storage.responses_table.insert_rows()