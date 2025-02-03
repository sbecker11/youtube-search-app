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

class YouTubeStorage:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YouTubeStorage, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if YouTubeStorage._instance is not None:
            raise RuntimeError("This class is a singleton! Use get_singleton() method to get the instance.")
        dynamodb_url = DYNAMODB_URL
        responses_config = self.load_config(RESPONSES_CONFIG_PATH)
        snippets_config = self.load_config(SNIPPETS_CONFIG_PATH)

        self.dynamodb = boto3.resource('dynamodb', endpoint_url=dynamodb_url)
        self.responses_table = YouTubeTable(responses_config)
        self.snippets_table = YouTubeTable(snippets_config)

    def load_config(self, config_path:str) -> Dict[str,str]:
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
                return config
        except FileNotFoundError as error:
            logger.error(f"Configuration file not found: {error}")
            raise
        except json.JSONDecodeError as error:
            logger.error(f"Error decoding JSON configuration: {error}")
            raise

    def find_all_subjects(self) -> List[str]:
        """ return a list of all distinct subjects found among all responses sorted by request submitted at ascending """
        logger.info("Querying all distinct subjects.")
        subjects = self.responses_table.query_table(
            "SELECT DISTINCT subject FROM {responses_table} ORDER BY requestSubmittedAt ASC",
            {"responses_table": self.responses_table.table_name})
        logger.info(f"Found subjects: {subjects}")
        return subjects

    def find_response_ids_by_subject(self, subject: str) -> List[str]:
        """ return a list of response_id that contained the given subject in its request """
        logger.info(f"Querying response IDs for subject: {subject}")
        response_ids = self.responses_table.query_table(
            "SELECT response_id FROM {responses_table} WHERE subject = '{subject}'",
            {"responses_table":self.responses_table.table_name, "subject":subject})
        logger.info(f"Found #response IDs: {len(response_ids)} for subject:{subject}")
        return response_ids

    def find_snippets_by_response_id(self, response_id: str) -> List[Dict[str, str]]:
        """ return a list of all snippets of a given response with the given response_id"""
        logger.info(f"Querying snippets for response ID: {response_id}")
        snippets = self.snippets_table.query_table(
            "SELECT * FROM {snippets_table} WHERE responseId = '{response_id}'",
            {"snippets_table":self.snippets_table.table_name, "response_id":response_id})
        logger.info(f"Found #snippets: {len(snippets)} for response_id:{response_id}")
        return snippets

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
        logger.info(f"Generated response row: {response_row}")
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
        logger.info(f"Generated snippet rows: {snippet_rows}")
        return snippet_rows

    def add_request_response(self, youtube_response: Dict[str, str], youtube_query: Dict[str, str]):
        """ Add a request and its response to the database """
        logger.info("Adding request and response to the database.")
        response_row = self.get_response_row(youtube_response, youtube_query)
        snippet_rows = self.get_snippet_rows(youtube_response, response_row['responseId'])

        # Add response row to the responses table
        self.responses_table.add_item(response_row)
        logger.info(f"Added response row: {response_row}")

        # Add snippet rows to the snippets table
        self.snippets_table.reset_batch()
        for snippet_row in snippet_rows:
            self.snippets_table.add_item_to_batch(snippet_row)
        self.snippets_table.flush_batch()
        logger.info(f"Added snippet rows: {snippet_rows}")

    @classmethod
    def get_singleton(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
