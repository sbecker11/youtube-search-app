from datetime import datetime
from googleapiclient.discovery import build
from youtube_storage import YouTubeStorage

class YouTubeQueryEngine:
    def __init__(self, api_key, responses_table_name=None, snippets_table_name=None, config_url=None, endpoint_url=None):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.youtube_storage = YouTubeStorage(responses_table_name, snippets_table_name, config_url, endpoint_url)

    def search(self, query: str, subject: str):
        request_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 25
        }
        request = self.youtube.search().list(**request_params)
        response = request.execute()
        youtube_query = {
            'subject': subject,
            'requestSubmittedAt': datetime.utcnow().isoformat(),
            **request_params
        }
        response_row = self.youtube_storage.get_response_row(response, youtube_query)
        self.youtube_storage.responses_table.insert_row(response_row)
        snippet_rows = self.youtube_storage.get_snippet_rows(response, response_row['responseId'])
        for row in snippet_rows:
            self.youtube_storage.snippets_table.insert_row(row)
        self.youtube_storage.responses_table.insert_rows()
        self.youtube_storage.snippets_table.insert_rows()