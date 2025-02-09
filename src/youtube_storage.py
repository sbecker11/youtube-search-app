import os
import json
import logging
from typing import List, Dict
from datetime import datetime
import uuid
import boto3
from dotenv import load_dotenv
from youtube_table import YouTubeTable
from dynamodb_utils import DynamoDbJsonUtils, DynamoDbDictUtils

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeStorageQueryException(Exception):
    pass
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

    def __init__(self, dynamodb_resource=None, dynamodb_client=None):

        if not hasattr(self, 'initialized'):
            self.initialized = False  # singleton logic to ensure that heavy initialization is done only once
        elif self.initialized:
            return

        self.dynamo_url = os.getenv('DYNAMODB_URL')
        self.responses_config_path = os.getenv('RESPONSES_CONFIG_PATH')
        self.snippets_config_path = os.getenv('SNIPPETS_CONFIG_PATH')

        if not self.dynamo_url or not self.responses_config_path or not self.snippets_config_path:
            raise ValueError("Environment variables for database configuration are not set.")

        self.responses_table_config = DynamoDbJsonUtils.load_json_file(self.responses_config_path)
        if not isinstance(self.responses_table_config, dict):
            raise RuntimeError("responses_table_config is not a dict!")

        self.snippets_table_config = DynamoDbJsonUtils.load_json_file(self.snippets_config_path)
        if not isinstance(self.snippets_table_config, dict):
            raise RuntimeError("snippets_table_config is not a dict!")

        self.dynamodb_resource = dynamodb_resource or boto3.resource('dynamodb', endpoint_url=self.dynamo_url)
        self.dynamodb_client = dynamodb_client or boto3.client('dynamodb', endpoint_url=self.dynamo_url)

        # create the tables or die
        try:
            self.responses_table = YouTubeTable(self.responses_table_config, dynamodb_resource=self.dynamodb_resource)
            self.tables[self.responses_table]
        except boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Responses table error:%s", {error})
            raise error
        try:
            self.snippets_table = YouTubeTable(self.snippets_table_config, dynamodb_resource=self.dynamodb_resource)
            self.tables[self.responses_table]
        except boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Snippets table error:%s", {error})
            raise error

        logger.info("the YouTubeStorage instance is now initialized with dynamoDb tables")

        self.initialized = True  # Flag to show heavy initialization has been done

    def get_tables(self) -> List[YouTubeTable]:
        return self.tables

    def count_num_tables(self) -> int:
        response = self.dynamodb_client.list_tables()
        table_count = len(response['TableNames'])
        return table_count

    def count_table_items(self, table_name:str) -> int:
        for table in self.get_tables():
            if table.get_table_name() == table_name:
                return table.count_items()
        return 0

    def find_all_querys(self) -> List[str]:
        """Return a list of all distinct querys found among all responses sorted by request submitted at ascending."""
        logger.info("Querying all distinct querys.")
        querys = self.responses_table.query_table(
            "SELECT DISTINCT query FROM {responses_table} ORDER BY requestSubmittedAt ASC",
            {"responses_table": self.responses_table.table_name})
        logger.info("Found %d unique querys", len(querys))
        return querys


    def find_response_ids_by_query(self, query: str) -> List[str]:
        """Return a list of response_id that contained the given query in its request."""
        logger.info("Querying response IDs for query: %s", query)

        response_ids = self.responses_table.query_table(
            "SELECT response_id FROM {responses_table} WHERE query = :query",
            {"responses_table": self.responses_table.table_name, ":query": query})  # Use parameters to avoid SQL injection
        logger.info("Found %d unique response IDs for query: %s", len(response_ids), query)
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
        """ This function takes a query_request object and its query_response object to create a flat dict of
            attribute/value pairs. The attribute/value pairs of this dict are preprocessed and will then be
            stored as a row of attributes in the "Reponses" dynamodb table. Each row having a unique response_id """
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
        print(f"response_row:\n{json.dumps(response_row,indent=2)}")
        pre_processed_response_row = self.responses_table.get_preprocessed_item(response_row)
        print(f"pre_processed_response_row:\n{json.dumps(pre_processed_response_row,indent=2)}")

        return pre_processed_response_row

    def get_snippet_rows(self, query_response: Dict[str, any], response_id: str) -> List[Dict[str, any]]:
        """ This function takes parent reponse_id and a query_response and extracts its list of associated
            items. Each item has a hierarchical snippet object. This object is transformed into a flattened
            dict of preprocessed attribute/value pairs. Each flattened dict will be stored as a row
            in the Snippets table in dynamodb."""
        pre_processed_snippet_rows = []
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
                'tags': snippet.get('tags', []),
                'liveBroadcastContent': snippet.get('liveBroadcastContent', ''),
                'publishTime': snippet.get('publishTime', '')
            }
            thumbnails = snippet.get('thumbnails', {})
            flattened_thumbnails = DynamoDbDictUtils.flatten_dict(
                current_dict=thumbnails,
                parent_key='thumbnails')
            for key,val in flattened_thumbnails.items():
                snippet_row[key] = val

            print(f"snippet_row:\n{json.dumps(snippet_row,indent=2)}")
            pre_processed_snippet_row = self.snippets_table.get_preprocessed_item(snippet_row)
            print(f"pre_processed_snippet_row:\n{json.dumps(pre_processed_snippet_row,indent=2)}")
            pre_processed_snippet_rows.append(pre_processed_snippet_row)

        logger.info("Generated %d pre_processed_snippet_rows for response ID: %s", len(pre_processed_snippet_rows), response_id)
        return pre_processed_snippet_rows

    def add_query_request_and_response(self, query_request: Dict[str, any], query_response: Dict[str, any]):
        """ Adds a query request and its query response object to the database. """
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
