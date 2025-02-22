import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import uuid
import boto3
from random import random, choice
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from youtube.youtube_table import YouTubeTable
from dynamodb_utils.json_utils import DynamoDbJsonUtils
from dynamodb_utils.dict_utils import DynamoDbDictUtils
from dynamodb_utils.dbtypes import DbTable, DbItem, DbIndex
from dynamodb_utils.item_utils import DynamoDbItemPreProcessor

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeStorageattrException(Exception):
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
            # use the response_table_config to create the resources YouTubeTable,
            # which creates a new dbTable if needed and then references it
            self.responses_table = YouTubeTable(self.responses_table_config)
            self.tables.append(self.responses_table)
        except boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Responses table error:%s", {error})
            raise error
        try:
            # use the snippets_table_config to create the Snippets YouTubeTable,
            # which creates a new dbTable if needed and then references it
            self.snippets_table = YouTubeTable(self.snippets_table_config)
            self.tables.append(self.snippets_table)
        except boto3.exceptions.Boto3Error as error:
            logger.error("failed attempt to create YouTubeTable for Snippets table error:%s", {error})
            raise error
        logger.info("the YouTubeStorage instance is now initialized with %d YouTubeTables", len(self.tables))

        self.initialized = True  # Flag to show heavy initialization has been done

    def get_tables(self) -> List[YouTubeTable]:
        return self.tables

    def get_table_by_name(self, table_name:str) -> YouTubeTable:
        """ returns the YouTubeTable with the given name """
        for table in self.get_tables():
            if table.get_table_name() == table_name:
                return table
        
    def scan_table_items(self, table_name:str) -> List[DbItem]:
        """ returns a list of all items in the given table """
        for table in self.get_tables():
            if table.get_table_name() == table_name:
                return table.scan_items()
        raise YouTubeStorageException(f"Table {table_name} not found.")

    def count_num_dbTables(self) -> int:
        response = self.dynamodb_client.list_tables()
        table_count = len(response['TableNames'])
        return table_count

    def count_table_items(self, table_name:str) -> int:
        for table in self.get_tables():
            if table.get_table_name() == table_name:
                return table.count_items()
        return 0
    
    def create_response_id(self) -> str:
        """ generates a unique response_id for each response """
        response_id = str(uuid.uuid4())
        # logger.info("Generated response_id: %s", response_id)
        return response_id
    
    def is_valid_response_id(self, response_id: str) -> bool:
        """ checks if the given response_id is a valid response_id """
        if not response_id:
            return False
        if not isinstance(response_id, str):
            return False
        if len(response_id) != 36:
            return False
        num_hyphens = response_id.count('-')
        if num_hyphens != 4:
            return False
        parts = response_id.split('-')
        if len(parts) != 5:
            return False
        for part in parts:
            if not part.isalnum():
                return False
        return True
    

    def dump_tables(self, json_file:str):
        if not json_file or not json_file.endswith(".json"):
            logger.error("output json_file undefined or is not a valid json file")
            raise YouTubeStorageException("output json_file undefined or is not a valid json file")
  
        logger.info(f"Ready to dump all data to json_file: {json_file}")
        
        """ dump the configs and all items of all tables into a single json_file"""
        alltables = {      
            "responses.table_config" : self.responses_table.get_table_config(),
            "responses.items" : self.responses_table.scan_items(),
            "snippets.table_config" : self.snippets_table.get_table_config(),
            "snippets.items" : self.snippets_table.scan_items()
        }
        DynamoDbJsonUtils.dump_json_file(alltables, json_file)

        logger.info("all tables dumped successfully!")


    def load_tables(self, json_file:str):
        if not json_file or not json_file.endswith(".json") or not os.path.exists(json_file):
            logger.error("input json_file undefined or is not a valid json file")
            raise YouTubeStorageException("input json_file undefined or is not a valid json file")

        logger.info(f"Ready to load all data from json_file: {json_file}")

        """ load all items of all tables from a single json_file"""
        alltables = DynamoDbJsonUtils.load_json_file(json_file)

        if not isinstance(alltables, dict):
            raise YouTubeStorageException("alltables is not a dict!")
        
        # verify that the tables exist or were just created by YouTubeTable
        if not self.responses_table.dbTable_exists():
            raise YouTubeStorageException("responses_table does not exist!")
        if self.snippets_table.dbTable_exists():
            raise YouTubeStorageException("snippets_table does not exist!")
                                                              
        # verify that the table configs match
        if self.responses.get_table_config() != alltables["responses.table_config"]:
            raise YouTubeStorageException("responses_table_config does not match!") 
        else:
            logger.info("loaded responses_table_config matches internal responses_table_config!")

        if self.snippets.get_table_config() != alltables["snippets.table_config"]:
            raise YouTubeStorageException("snippets_table_config does not match!")
        else:
            logger.info("loaded snippets_table_config matches internal snippets_table_config!")
        
        # load all items maintaining idemotency and avoiding duplicates
        self.responses_table.load_items(alltables["responses.items"], idempotent=True)
        logger.info("loaded %d items into the Responses table", len(alltables["responses.items"]))

        self.snippets_table.load_items(alltables["snippets.items"], itempotent=True)
        logger.info("loaded %d items into the Snippets table", len(alltables["snippets.items"]))

        logger.info("all tables loaded successfully!")

    def make_response_row(self, attr_request: Dict[str, any], query_response: Dict[str, str]) -> Dict[str, any]:
        """ This function takes a attr_request object and its query_response object to create a flat dict of
            attribute/value pairs. The attribute/value pairs of this dict are preprocessed and will then be
            stored as a row of attributes in the "Reponses" dynamodb table. Each row having a unique etag """
        response_id = self.create_response_id()
        # logger.info("Generated response_id: %s", response_id)")
        response_row = {
            'response_id': response_id,  # PK refernced by Snippets.response_id (FK)
            'etag': query_response.get('etag', ''),
            'kind': query_response.get('kind', ''),
            "nextPageToken": query_response.get('nextPageToken', ''),
            "regionCode": query_response.get('regionCode', ''),
            "pageInfo": {
                "totalResults": query_response.get('pageInfo', {}).get('totalResults', 0),
                "resultsPerPage": query_response.get('pageInfo', {}).get('resultsPerPage', 0)
            },
            "requestSubmittedAt": attr_request.get('requestSubmittedAt', datetime.utcnow().isoformat()),
            "responseReceivedAt": datetime.utcnow().isoformat(),
            "queryDetails": {
                "part": attr_request.get('part', ''),
                "q": attr_request.get('q', ''),
                "type": attr_request.get('type', ''),
                "maxResults": attr_request.get('maxResults', ''),
                "query": attr_request.get('query', '')
            }
        }
        # logger.info("Generated response row with response_id: %s", response_id)
        # print(f"response_row:\n{json.dumps(response_row,indent=2)}")
        flattened_response_row = DynamoDbDictUtils.flatten_dict(
                current_dict=response_row,
                parent_key='')
        marked_resonse_row = DynamoDbItemPreProcessor.set_marked_preprocessed_item(flattened_response_row)
        if not DynamoDbItemPreProcessor.is_marked_preprocessed_item(marked_resonse_row):
            DynamoDbItemPreProcessor.print_invalid_item(marked_resonse_row)
            raise YouTubeStorageException("flattened_response_row is not a preprocessed item")
        return marked_resonse_row

    def make_snippet_rows(self, query_response: Dict[str, any], response_id: str) -> List[Dict[str, any]]:
        """ This function takes parent reponse_id and a query_response and extracts its list of associated
            items. Each item has a hierarchical snippet object. This object is transformed into a flattened
            dict of preprocessed attribute/value pairs. Each flattened dict will be stored as a row
            in the Snippets table in dynamodb."""
        pre_processed_snippet_rows = []
        for item in query_response.get('items', []):
            snippet = item.get('snippet', {})
            snippet_row = {
                'response_id': response_id,  # FK to responses_table
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
            if not DynamoDbItemPreProcessor.is_marked_preprocessed_item(pre_processed_snippet_row):
                DynamoDbItemPreProcessor.print_invalid_item(pre_processed_snippet_row)
                raise YouTubeStorageException("pre_processed_snippet_row is not a preprocessed item")
            pre_processed_snippet_rows.append(pre_processed_snippet_row)

        # logger.info("Generated %d pre_processed_snippet_rows for response ID: %s", len(pre_processed_snippet_rows), response_id)
        return pre_processed_snippet_rows

    def add_query_request_and_response(self, query_request: Dict[str, any], query_response: Dict[str, any]):
        """ Adds a query request and its query response object to the database. """
        # logger.info("computing response_row from query_request and query_response.")
        response_row = self.make_response_row(query_request, query_response)
        if not DynamoDbItemPreProcessor.is_marked_preprocessed_item(response_row):
            DynamoDbItemPreProcessor.print_invalid_item(response_row)
            raise YouTubeStorageException("response_row is not a preprocessed item")
        if 'response_id' not in response_row:
            raise YouTubeStorageException(f"response_row does not contain a response_id response_row: {response_row}")

        response_id = response_row['response_id']

        # logger.info("computing snippet_rows from query_response.")
        snippet_rows = self.make_snippet_rows(query_response, response_row['response_id'])
        for snippet_row in snippet_rows:
            if not DynamoDbItemPreProcessor.is_marked_preprocessed_item(snippet_row):
                DynamoDbItemPreProcessor.print_invalid_item(snippet_row)
                raise YouTubeStorageException("snippet_row is not a preprocessed item")
            if 'response_id' not in snippet_row:
                raise YouTubeStorageException(f"snippet_row does not contain a response_id snippet_row: {snippet_row}")

        try:
            # Add response row to the responses table (not batched) in idempotent fashion
            self.responses_table.add_item(response_row, idempotent=True)
            # logger.info("Added response row with ID: %s", response_row['response_id'])

            # Add snippet rows to the snippets table using a batch writer
            self.snippets_table.add_items(snippet_rows, idempotent=True)
            # logger.info("Added %d snippet rows for response ID: %s", len(snippet_rows), response_row['response_id'])

        except boto3.exceptions.Boto3Error as error:
            logger.error("Failed to add request and response to database: %s", str(error))
            raise error
            # Consider implementing retry logic here if it's apattrriate for your use case.

    ##################################################################################
    # Query functions for the YouTubeStorage class on YouTubeTables

    def get_item_hashkey(dbItem:DbItem, key_attr_names:List[str]) -> str:
        """ an example get_item_key function that returns a hashkey
            from a composite list of attr values
        """
        parts = []
        for key_attr_name in key_attr_names:
            key_attr_value = dbItem.get(key_attr_name)
            if key_attr_value:
                part = f"{key_attr_name}:{key_attr_value}"
                parts.append(part)
        composite = "-".join(parts)
        hash_int = hash(composite)
        hash_key = str(hash_int)
        return hash_key
    
    def get_item_attribute(dbItem:DbItem, attribute:str) -> str:
        return dbItem.get(attribute)

    def create_key_indexed_items(self, dbItems: List[DbItem], get_item_key) -> DbIndex:
        """ use a get_item_key function to create an index of the given dbItems.
            if the key is already in use, then create a list to hold all dbItems
            that share that key and set the value of the key to the list of
            items.
        """
        key_indexed_items = {} # this a Dict[str,Any] where Any can be DbItem or list[DbItem]
        for dbItem in dbItems:
            key = get_item_key(dbItem)

            # handle collision : replace key value with a list of DbItems with that key #
            if key in key_indexed_items:
                current_value = key_indexed_items[key]
                if isinstance(current_value, list):
                    current_items_list = current_value
                    current_items_list.append(dbItem)
                    key_indexed_items[key] = current_items_list
                if isinstance(current_value, DbItem):
                    new_items_list = list(current_value, dbItem)
                    key_indexed_items[key] = new_items_list
            else:
                key_indexed_items[key] = dbItem
        return key_indexed_items

    def create_attribute_indexed_items(self, dbItems:List[DbItem], attribute:str) -> DbIndex:
        def get_item_key_func(dbItem): return dbItem[attribute]
        return self.create_key_indexed_items(dbItems, get_item_key_func)

    def create_key_sorted_items(self, index:DbIndex, get_item_key_func) -> List[DbItem]:
        """Sort the index using get_item_key(item) for each item."""
        key_sorted_items = sorted(index.values(), key=lambda x: get_item_key_func(x))
        return key_sorted_items
    
    ###########################################################################3
    # Non-indexed query functions
    
    def find_items_by_attribute(self, dbTable:DbTable, attribute_index: DbIndex, attribute: str) -> List[DbItem]:
        """Find a dbItem by its attribute."""
        if attribute_index:
            return attribute_index.get(attribute)
        elif dbTable:
            return dbTable.find_items_by_attribute(attribute)
        else:
            raise YouTubeStorageException("No attribute index or dbTable provided.")

if __name__ == "__main__":
    storage = YouTubeStorage.get_singleton()
    logger.info("num_dbTables:%d", storage.count_num_dbTables())
    storage.test_create_etag_indexed_items()
    storage.test_get_publishedAt_sorted_items_in_date_range()


