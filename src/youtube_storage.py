import os
import json
import logging
from typing import List, Dict
from datetime import datetime
import uuid
import boto3
from dotenv import load_dotenv
from youtube_table import YouTubeTable

load_dotenv()

DYNAMODB_URL = os.getenv('DYNAMODB_URL')
RESPONSES_CONFIG_PATH = os.getenv('RESPONSES_CONFIG_PATH')
SNIPPETS_CONFIG_PATH = os.getenv('SNIPPETS_CONFIG_PATH')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeStorageException(Exception):
    pass
class YouTubeStorage:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YouTubeStorage, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if YouTubeStorage._instance is not None:
            raise RuntimeError("This class is a singleton! Use get_singleton() method to get the instance.")

        if not DYNAMODB_URL or not RESPONSES_CONFIG_PATH or not SNIPPETS_CONFIG_PATH:
            raise ValueError("Environment variables for database configuration are not set.")

        dynamodb_url = DYNAMODB_URL
        responses_config = self.load_config(RESPONSES_CONFIG_PATH)
        snippets_config = self.load_config(SNIPPETS_CONFIG_PATH)

        self.dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_url)
        self.responses_table = YouTubeTable(responses_config)
        self.snippets_table = YouTubeTable(snippets_config)

    def load_config(self, config_path: str) -> Dict[str, any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
                return config
        except FileNotFoundError:
            logger.error("Configuration file not found at %s:", config_path)
            return {}  # Return empty dict instead of raising an exception
        except json.JSONDecodeError as error:
            logger.error("Error decoding JSON configuration file at %s: %s", config_path, error)
            return {}

    def find_all_subjects(self) -> List[str]:
        """Return a list of all distinct subjects found among all responses sorted by request submitted at ascending."""
        logger.info("Querying all distinct subjects.")
        subjects = self.responses_table.query_table(
            "SELECT DISTINCT subject FROM {responses_table} ORDER BY requestSubmittedAt ASC",
            {"responses_table": self.responses_table.table_name})
        logger.info("Found subjects: %d", len(subjects))
        return subjects

    def find_response_ids_by_subject(self, subject: str) -> List[str]:
        """Return a list of response_id that contained the given subject in its request."""
        logger.info("Querying response IDs for subject: %s", subject)
        response_ids = self.responses_table.query_table(
            "SELECT response_id FROM {responses_table} WHERE subject = :subject",
            {"responses_table": self.responses_table.table_name, ":subject": subject})  # Use parameters to avoid SQL injection
        logger.info("Found %d response IDs for subject: %s", len(response_ids), subject)
        return response_ids

    def find_snippets_by_response_id(self, response_id: str) -> List[Dict[str, str]]:
        """Return a list of all snippets of a given response with the given response_id."""
        logger.info("Querying snippets for response ID: %s", response_id)
        snippets = self.snippets_table.query_table(
            "SELECT * FROM {snippets_table} WHERE responseId = :response_id",
            {"snippets_table": self.snippets_table.table_name, ":response_id": response_id})  # Use parameters here too
        logger.info("Found %d snippets for response_id: %s", len(snippets), response_id)
        return snippets

    def get_response_row(self, youtube_response: Dict[str, any], youtube_query: Dict[str, str]) -> Dict[str, any]:
        response_id = str(uuid.uuid4())  # Generate a unique primary key
        response_row = {
            'responseId': response_id,  # PK
            'etag': youtube_response.get('etag', ''),
            'kind': youtube_response.get('kind', ''),
            "nextPageToken": youtube_response.get('nextPageToken', ''),
            "regionCode": youtube_response.get('regionCode', ''),
            "pageInfo": {
                "totalResults": youtube_response.get('pageInfo', {}).get('totalResults', 0),
                "resultsPerPage": youtube_response.get('pageInfo', {}).get('resultsPerPage', 0)
            },
            "subject": youtube_query.get('subject', ''),
            "requestSubmittedAt": youtube_query.get('requestSubmittedAt', datetime.utcnow().isoformat()),
            "responseReceivedAt": datetime.utcnow().isoformat(),
            "query": {
                "part": youtube_query.get('part', ''),
                "q": youtube_query.get('q', ''),
                "type": youtube_query.get('type', ''),
                "maxResults": youtube_query.get('maxResults', '')
            }
        }
        logger.info("Generated response row with ID: %s", response_id)
        return response_row

    def get_snippet_rows(self, youtube_response: Dict[str, any], response_id: str) -> List[Dict[str, any]]:
        snippet_rows = []
        for item in youtube_response.get('items', []):
            snippet = item.get('snippet', {})
            snippet_row = {
                'responseId': response_id,  # FK to responses_table
                'videoId': item.get('id', {}).get('videoId', ''),
                'publishedAt': snippet.get('publishedAt', ''),
                'channelId': snippet.get('channelId', ''),
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channelTitle': snippet.get('channelTitle', ''),
                'tags': snippet.get('tags', [])
            }
            snippet_rows.append(snippet_row)
        logger.info("Generated %d snippet rows for response ID: %s", len(snippet_rows), response_id)
        return snippet_rows

    def add_request_response(self, youtube_response: Dict[str, any], youtube_query: Dict[str, str]):
        """Add a request and its response to the database."""
        logger.info("Adding request and response to the database.")
        response_row = self.get_response_row(youtube_response, youtube_query)
        snippet_rows = self.get_snippet_rows(youtube_response, response_row['responseId'])

        try:
            # Add response row to the responses table
            self.responses_table.add_item(response_row)
            logger.info("Added response row with ID: %s", response_row['responseId'])

            # Add snippet rows to the snippets table
            self.snippets_table.reset_batch()
            for snippet_row in snippet_rows:
                self.snippets_table.add_item_to_batch(snippet_row)
            self.snippets_table.flush_batch()

            logger.info("Added %d snippet rows for response ID: %s", len(snippet_rows), response_row['responseId'])
        except boto3.exceptions.Boto3Error as error:
            logger.error("Failed to add request and response to database: %s", str(error))
            # Consider implementing retry logic here if it's appropriate for your use case.

    @classmethod
    def get_singleton(cls) -> 'YouTubeStorage':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
