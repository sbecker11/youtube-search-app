import os
import json
import logging
from typing import List, Dict
from datetime import datetime
import uuid
import boto3
from dotenv import load_dotenv
from youtube_table import YouTubeTable, DbTable
from dynamodb_utils.json_utils import DynamoDbJsonUtils
from dynamodb_utils.dict_utils import DynamoDbDictUtils
from dynamodb_utils.dbtypes import *

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

        # for higher-level dynamodb functions
        self.dynamodb_resource = dynamodb_resource or boto3.resource('dynamodb', endpoint_url=self.dynamo_url)

        # for lower-level dynamodb functions
        self.dynamodb_client = dynamodb_client or boto3.client('dynamodb', endpoint_url=self.dynamo_url)

        # create the YouTubeTables or die
        self.tables = []
        try:
            self.responses_table = YouTubeTable(self.responses_table_config)
            self.tables.append(self.responses_table)
        except boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Responses table error:%s", {error})
            raise error
        try:
            self.snippets_table = YouTubeTable(self.snippets_table_config)
            self.tables.append(self.snippets_table)
        except boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Snippets table error:%s", {error})
            raise error
        logger.info("the YouTubeStorage instance is now initialized with %d YouTubeTables", len(self.tables))

        self.initialized = True  # Flag to show heavy initialization has been done

    def get_tables(self) -> List[YouTubeTable]:
        return self.tables


    def count_num_dbTables(self) -> int:
        response = self.dynamodb_client.list_tables()
        table_count = len(response['TableNames'])
        return table_count

    def count_table_items(self, table_name:str) -> int:
        for table in self.get_tables():
            if table.get_table_name() == table_name:
                return table.count_items()
        return 0

    def find_all_distinct_querys(self) -> List[str]:
        """Return a list of all distinct querys found among all responses sorted alphabetically."""
        logger.info("Querying all distinct querys.")
        responses_table = self.responses_table
        all_responseItems = responses_table.scan_table()
        if not all_responseItems:
            logger.warning("theresponses_table is empty")
            return []

        # extra validation
        responseItem0 = all_responseItems[0]
        responseItem0_text = DynamoDbJsonUtils.json_dumps(responseItem0)
        recreatedResponseItem0 = json.loads(responseItem0_text)
        print(responseItem0_text)
        query_dbAttr = "queryDetails.q"
        select_by_dbAttrs = [query_dbAttr]
        if query_dbAttr not in recreatedResponseItem0:
            raise RuntimeError(f"select_by_dbAttrs NOT found in {json.dumps(recreatedResponseItem0)}")

        filtered_dbItems = responses_table.select_dbItems_by_dbAttrs(all_responseItems, select_by_dbAttrs)
        distinct_values = {}
        for dbAttr in select_by_dbAttrs:
            distinct_values[dbAttr] = set([dbItem[dbAttr] for dbItem in filtered_dbItems if dbAttr in dbItem])

        distinct_queries = list(distinct_values[query_dbAttr])
        logger.info("Found %d distinct querys", len(distinct_queries))
        logger.info(f"distinct querys {distinct_queries}")

        return distinct_queries


    def find_distinct_request_queries(self):
        logger.info("Finding all distinct request queries.")
        responses_table = self.responses_table
        response_dbItems = responses_table.scan_table()
        query_dbAttr = "queryDetails.q"
        filter_by_dbAttrs = [query_dbAttr]
        distinct_values_by_dbAttr = self.find_distinct_dbItem_values_over_dbAttrs(response_dbItems, filter_by_dbAttrs)
        distinct_query_values = distinct_values_by_dbAttr[query_dbAttr]
        logger.info("Found distinct request queries: {distinct_query_values}")
        fast_api_response = {}
        pos = 0
        for distinct_query_value in distinct_query_values:
            fast_api_response[pos] = distinct_query_value
            post += 1
        logger.info(f"fast_api_response: {json.dumps(fast_api_response,inden=4)}" )
        return fast_api_response

    # this is used only by find_distinct_request_queries
    def find_distinct_dbItem_values_over_dbAttrs(self, dbItems:List[DbItem], filter_by_dbAttrs:List[DbAttr]) -> Dict[DbAttr,Any]:
        """Return a list of all distinct values of filter_by_dbAttrs found over the given dbItems."""
        target_dbItem = dbItems[0]
        target_dbItem_text = DynamoDbJsonUtils.json_dumps(target_dbItem)
        target_dbItem_recon_dict = json.loads(target_dbItem_text)
        for filter_by_dbAttr in filter_by_dbAttrs:
            if filter_by_dbAttr not in target_dbItem_recon_dict:
                raise RuntimeError(f"find_distinct_dbItem_values_over_dbAttrs dbAtt:{filter_by_dbAttr} NOT found in {json.dumps(target_dbItem_recon_dict)}")
        filtered_dbItems = responses_table.select_dbItems_by_dbAttrs(all_responseItems, select_by_dbAttrs)
        distinct_values_by_dbAttr = {}
        for dbAttr in select_by_dbAttrs:
            distinct_values_by_dbAttr[dbAttr] = set([ dbItem[dbAttr] for dbItem in filtered_dbItems ])
        return distinct_values_by_dbAttr

    def find_response_ids_by_query(self, query: str) -> List[str]:
        logger.warning("NOT YET IMPLEMENTED")
        return []

        # """Return a list of response_id that contained the given query in its request."""
        # logger.info("Querying response IDs for query: %s", query)

        # response_ids = self.responses_table.query_table(
        #     "SELECT response_id FROM {responses_table} WHERE query = :query",
        #     {"responses_table": self.responses_table.table_name, ":query": query})  # Use parameters to avoid SQL injection
        # logger.info("Found %d unique response IDs for query: %s", len(response_ids), query)
        # return response_ids

    def find_snippets_by_response_id(self, response_id: str) -> List[Dict[str, str]]:
        logger.warning("NET YET IMPLEMENTED")
        return []

        # """Return a list of all snippets of a given response with the given response_id."""
        # logger.info("Querying snippets for response ID: %s", response_id)
        # snippets = self.snippets_table.query_table(
        #     "SELECT * FROM {snippets_table} WHERE responseId = :response_id",
        #     {"snippets_table": self.snippets_table.table_name, ":response_id": response_id})  # Use parameters here too
        # logger.info("Found %d snippets for response_id: %s", len(snippets), response_id)
        # return snippets

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
        pre_processed_response_row = self.responses_table.item_preprocessor.get_preprocessed_item(response_row)
        flattened_response_row = DynamoDbDictUtils.flatten_dict(
                current_dict=pre_processed_response_row,
                parent_key='')
        print(f"flattened_response_row:\n{json.dumps(flattened_response_row,indent=2)}")

        return flattened_response_row

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

            # print(f"snippet_row:\n{json.dumps(snippet_row,indent=2)}")
            pre_processed_snippet_row = self.snippets_table.item_preprocessor.get_preprocessed_item(snippet_row)
            # print(f"pre_processed_snippet_row:\n{json.dumps(pre_processed_snippet_row,indent=2)}")
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

if __name__ == "__main__":
    storage = YouTubeStorage.get_singleton()
    logger.info("num_dbTables:%d",storage.count_num_dbTables())
