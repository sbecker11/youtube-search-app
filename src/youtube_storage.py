from typing import List, Dict
from datetime import datetime
import uuid
import requests
from youtube_table import YouTubeTable

class YouTubeStorage:
    def __init__(self,
                 responses_table_name=None,
                 snippets_table_name=None,
                 config_url=None,
                 endpoint_url=None):
        if config_url:
            try:
                response = requests.get(config_url, timeout=10)
                response.raise_for_status()  # Raise an HTTPError for bad responses
                config = response.json()
                responses_table_name = config['ResponsesTableName']
                snippets_table_name = config['SnippetsTableName']
            except requests.exceptions.RequestException as error:
                print(f"An error occurred while fetching the config from config_url:{config_url}:{error}")
            except ValueError:
                print(f"The response from config_url:{config_url} did not contain valid JSON.")
            except KeyError as error:
                print(f"Missing expected config property from config_url:{config_url}:{error}")
        self.responses_table = YouTubeTable(responses_table_name, endpoint_url=endpoint_url)
        self.snippets_table = YouTubeTable(snippets_table_name, endpoint_url=endpoint_url)

    def get_response_row(self, youtube_response: Dict[str, str], youtube_query: Dict[str, str]) -> Dict[str, str]:
        response_id = str(uuid.uuid4())  # Generate a unique primary key
        response_row = {
            'responseId': response_id,  # PK
            'etag': youtube_response['etag'],
            'kind': youtube_response['kind'],
            "nextPageToken": youtube_response['nextPageToken'],
            "regionCode": youtube_response['regionCode'],
            "pageInfo.totalResults": youtube_response['pageInfo']['totalResults'],
            "pageInfo.resultsPerPage": youtube_response['pageInfo']['resultsPerPage'],
            "subject": youtube_query['subject'],
            "requestSubmittedAt": youtube_query['requestSubmittedAt'],
            "responseReceivedAt": datetime.utcnow().isoformat(),
            "query.part": youtube_query['part'],
            "query.q": youtube_query['q'],
            "query.type": youtube_query['type'],
            "query.maxResults": youtube_query['maxResults']
        }
        return response_row

    def get_snippet_rows(self, youtube_response, response_id) -> List[Dict[str, str]]:
        snippet_rows = []
        for item in youtube_response.get('items', []):
            snippet = item.get('snippet', {})
            snippet_row = {
                'responseId': response_id,  # FK to responses_table
                'videoId': item['id']['videoId'],
                'publishedAt': snippet['publishedAt'],
                'channelId': snippet['channelId'],
                'title': snippet['title'],
                'description': snippet['description'],
                'channelTitle': snippet['channelTitle'],
                'tags': snippet.get('tags', [])
            }
            snippet_rows.append(snippet_row)
        return snippet_rows