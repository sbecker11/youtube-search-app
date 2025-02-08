import os
import json
import logging
from typing import List, Dict
from datetime import datetime
import uuid
import boto3
from dotenv import load_dotenv
from youtube_table import YouTubeTable
from dynamodb_item_preprocessor import DynamoDBItemPreProcessor

load_dotenv()

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

    @classmethod
    def get_singleton(cls) -> 'YouTubeStorage':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):

        if not hasattr(self, 'initialized'):
            self.initialized = False  # singleton logic to ensure that heavy initialization is done only once
        elif self.initialized:
            return

        self.dynamo_url = os.getenv('DYNAMODB_URL')
        self.responses_config_path = os.getenv('RESPONSES_CONFIG_PATH')
        self.snippets_config_path = os.getenv('SNIPPETS_CONFIG_PATH')

        if not self.dynamo_url or not self.responses_config_path or not self.snippets_config_path:
            raise ValueError("Environment variables for database configuration are not set.")

        self.responses_table_config = self.load_json_file(self.responses_config_path)
        if not isinstance(self.responses_table_config, dict):
            raise RuntimeError("responses_table_config is not a dict!")
        self.response_item_preprocessor = \
            DynamoDBItemPreProcessor(self.responses_table_config, attribute_name_prefix="responses.")

        self.snippets_table_config = self.load_json_file(self.snippets_config_path)
        if not isinstance(self.snippets_table_config, dict):
            raise RuntimeError("snippets_table_config is not a dict!")
        self.snippet_item_preprocessor = \
            DynamoDBItemPreProcessor(self.snippets_table_config, attribute_name_prefix="snippets.")

        # creating dynamodb resource
        self.dynamodb = boto3.resource('dynamodb', endpoint_url=self.dynamo_url)

        try:
            self.responses_table = YouTubeTable(self.responses_table_config)
        except  boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Responses table error:%s", {error})
            raise error
        try:
            self.snippets_table = YouTubeTable(self.snippets_table_config)
        except  boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Snippets table error:%s", {error})
            raise error

        logger.info("the YouTubeStorage instance is now initialized with dynamoDb tables")

        self.initialized = True  # Flag to show heavy initialization has been done

    def load_json_file(self, json_file_path: str) -> Dict[str, any]:
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error("JSON file not found at %s:", json_file_path)
            return {}  # Return empty dict instead of raising an exception
        except json.JSONDecodeError as error:
            logger.error("Error decoding JSON file at %s: %s", json_file_path, error)
            return {}

    def find_all_querys(self) -> List[str]:
        """Return a list of all distinct querys found among all responses sorted by request submitted at ascending."""
        logger.info("Querying all distinct querys.")
        querys = self.responses_table.query_table(
            "SELECT DISTINCT query FROM {responses_table} ORDER BY requestSubmittedAt ASC",
            {"responses_table": self.responses_table.table_name})
        logger.info("Found querys: %d", len(querys))
        return querys

    def find_response_ids_by_query(self, query: str) -> List[str]:
        """Return a list of response_id that contained the given query in its request."""
        logger.info("Querying response IDs for query: %s", query)
        response_ids = self.responses_table.query_table(
            "SELECT response_id FROM {responses_table} WHERE query = :query",
            {"responses_table": self.responses_table.table_name, ":query": query})  # Use parameters to avoid SQL injection
        logger.info("Found %d response IDs for query: %s", len(response_ids), query)
        return response_ids

    def find_snippets_by_response_id(self, response_id: str) -> List[Dict[str, str]]:
        """Return a list of all snippets of a given response with the given response_id."""
        logger.info("Querying snippets for response ID: %s", response_id)
        snippets = self.snippets_table.query_table(
            "SELECT * FROM {snippets_table} WHERE responseId = :response_id",
            {"snippets_table": self.snippets_table.table_name, ":response_id": response_id})  # Use parameters here too
        logger.info("Found %d snippets for response_id: %s", len(snippets), response_id)
        return snippets

    def get_response_row(self, query_request: Dict[str, any], query_response: Dict[str, str]) -> Dict[str, any]:
        response_id = str(uuid.uuid4())  # Generate a unique primary key
        response_row = {
            'responseId': response_id,  # PK
            'etag': query_response.get('etag', ''),
            'kind': query_response.get('kind', ''),
            "nextPageToken": query_response.get('nextPageToken', ''),
            "regionCode": query_response.get('regionCode', ''),
            "pageInfo": {
                "totalResults": query_response.get('pageInfo', {}).get('totalResults', 0),
                "resultsPerPage": query_response.get('pageInfo', {}).get('resultsPerPage', 0)
            },
            "requestSubmittedAt": query_request.get('requestSubmittedAt', datetime.utcnow().isoformat()),
            "responseReceivedAt": datetime.utcnow().isoformat(),
            "queryDetails": {
                "part": query_request.get('part', ''),
                "q": query_request.get('q', ''),
                "type": query_request.get('type', ''),
                "maxResults": query_request.get('maxResults', ''),
                "query": query_request.get('query', '')
            }
        }
        logger.info("Generated response row with ID: %s", response_id)
        processed_response_row = self.response_item_preprocessor.process_item(response_row)
        return processed_response_row

    def get_snippet_rows(self, query_response: Dict[str, any], response_id: str) -> List[Dict[str, any]]:
        processed_snippet_rows = []
        for item in query_response.get('items', []):
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
            processed_snippet_row = self.snippet_item_preprocessor.process_item(snippet_row)
            processed_snippet_rows.append(processed_snippet_row)

        logger.info("Generated %d processed_snippet_rows for response ID: %s", len(processed_snippet_rows), response_id)
        return processed_snippet_rows

    def add_query_request_and_response(self, query_request: Dict[str, any], query_response: Dict[str, any]):
        """Add a request and its response to the database."""
        logger.info("computing response_row from query_request and query_response.")
        response_row = self.get_response_row(query_request, query_response)

        logger.info("computing snippet_rows from query_response.")
        snippet_rows = self.get_snippet_rows(query_response, response_row['responseId'])

        try:
            # Add response row to the responses table (not batched)
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
