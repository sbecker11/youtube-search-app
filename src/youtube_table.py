# pylint: disable=C0103 # Invalid name

import json
import logging
import os
from typing import Dict, Any, List

import boto3
import botocore
from boto3.resources.base import ServiceResource

from dynamodb_utils.item_utils import DynamoDbItemPreProcessor
from dynamodb_utils.json_utils import DynamoDbJsonUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DbItem = Dict[str, Any]
DbTable = ServiceResource

class YouTubeTableException(Exception):
    pass

class YouTubeTable:
    try:
        dynamodb_url = os.getenv('DYNAMODB_URL')
        dynamodb_client = boto3.client('dynamodb', endpoint_url=dynamodb_url)
        dynamodb_resource = boto3.resource('dynamodb', endpoint_url=dynamodb_url)
    except boto3.exceptions.Boto3Error as error:
        logger.error("class initialization error: %s", {error})
        raise

    def __init__(self, table_config: Dict[str, str]):
        try:
            self.table_config = table_config
            self.table_name = self.table_config['TableName']
            self.dbTable = YouTubeTable.find_dbTable_by_name(self.table_name)
            if not self.dbTable:
                self.dbTable = YouTubeTable.create_dbTable(self.table_config)

            self.item_preprocessor = DynamoDbItemPreProcessor(self.table_config)

            # initialize the batch list
            self.items_to_add = []

        except boto3.exceptions.Boto3Error as error:
            print(f"Error initializing DynamoDb resource: {error}")
            raise
        except FileNotFoundError as error:
            print(f"Configuration file not found: {error}")
            raise
        except json.JSONDecodeError as error:
            print(f"Error decoding JSON configuration: {error}")
            raise

        logger.info("YouTubeTable '%s' successfully initialized", self.table_name)

    def dbTable_exists(self):
        """
        Check if the dynamoDb table already exists.

        :return: True if the dynamoDb table exists, False otherwise.
        """
        try:
            self.dynamodb_client.describe_table(TableName=self.table_name)
            return True
        except self.dynamodb_client.exceptions.ResourceNotFoundException:
            return False
        except Exception as error:
            print(f"Error checking if dynamoDb table exists: {error}")
            raise

    def get_self_table_name(self) -> str:
        return self.table_name

    def get_self_preprocessed_item(self, item: DbItem) -> DbItem:
        return self.item_preprocessor.get_preprocessed_item(item)

    @classmethod
    def find_dbTable_by_name(cls, table_name: str) -> DbTable:
        """
        Find a DynamoDb table by its name, or return None

        :param table_name: The name of the table to check for existence.
        :return: The table if it exists, None otherwise.
        """
        found_dbTable = None
        try:
            # Attempt to describe the table. If this succeeds, the table exists.
            cls.dynamodb_client.describe_table(TableName=table_name)
            found_dbTable = cls.dynamodb_resource.Table(table_name)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ResourceNotFoundException':
                found_dbTable = None
            else:
                logger.error("An error occurred while checking for table %s: %s", table_name, error)
                return None
            # If the table doesn't exist, we'll get this exception.
            found_dbTable = None
        except boto3.exceptions.Boto3Error as error:
            # Catch other exceptions and log them for debugging.
            print(f"An error occurred while checking for table {table_name}: {error}")
            found_dbTable = None

        return found_dbTable

    @classmethod
    def create_dbTable(cls, dbTable_config: Dict[str,Any]) -> DbTable:
        """
        Create a new DynamoDb table with the given configuration.

        The configuration should include:
        - TableName
        - KeySchema: Specifies the attributes that make up the primary key for the table.
        - AttributeDefinitions: An array of attributes that describe the key schema for the table and indexes.
        - ProvisionedThroughput: Specifies the read and write capacity units for the table.

        Example configuration:
        {
            "TableName": "Responses",
            "KeySchema": [
                {
                    "AttributeName": "id",
                    "KeyType": "HASH"
                }
            ],
            "AttributeDefinitions": [
                {
                    "AttributeName": "id",
                    "AttributeType": "S"
                }
            ],
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        }
        """
        try:
            dbTable_name = dbTable_config["TableName"]
            new_dbTable = cls.dynamodb_resource.create_table(**dbTable_config)
            return new_dbTable
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in create_dbTable table: %s: %s", dbTable_name, {error})
            raise

    @classmethod
    def extract_dbTable_config(cls, dbTable_name: str) -> Dict[str, Any]:
        try:
            response = cls.dynamodb_client.describe_table(TableName=dbTable_name)
            table_description = response['Table']

            # Extracting key components of the table configuration:
            config = {
                'TableName': table_description['TableName'],
                'KeySchema': table_description['KeySchema'],
                'AttributeDefinitions': table_description['AttributeDefinitions'],
                'ProvisionedThroughput': table_description.get('ProvisionedThroughput', {}),
                # Including Global Secondary Indexes if present
                'GlobalSecondaryIndexes': table_description.get('GlobalSecondaryIndexes', []),
                # Including Local Secondary Indexes if present
                'LocalSecondaryIndexes': table_description.get('LocalSecondaryIndexes', [])
            }

            # Note: You might want to include other parameters based on your needs,
            # like BillingMode, StreamSpecification, etc., if they are defined for the table.

            return config
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"dbTable {dbTable_name} not found.")
            return {}
        except Exception as e:
            print(f"An error occurred: {e}")
            return {}


    @classmethod
    def add_item_to_dbTable(cls, item: DbItem, dbTable:DbTable):
        """
        Add a new DbItem to the dbTable.

        :param item: A dictionary representing the item to add.
        :param dbTable: that DbTable
        """
        try:
            dbTable.put_item(Item=item)
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in add_item_to_dbTable: %s: %s", dbTable.table_name, {error})
            raise

    def add_item_to_self(self, item: DbItem):
        """
        Add a new DbItem to the dbTable of this YouTubeTable.
        """
        YouTubeTable.add_item_to_dbTable(item, self.dbTable)

    @classmethod
    def add_item_to_dbTable_batch(cls, dbTable_batch:List[DbItem], item: DbItem):
        """
        Add an item to the dbTable_batch.

        :param item: a DbItem which is a dict representing the item to add.
        """
        try:
            dbTable_batch.append(item)
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in add_item_to_dbTable_batch for dbTable: %s: %s", dbTable.table_name, {error})
            raise

    def add_item_to_self_batch(self, item: DbItem):
        YouTubeTable.add_item_to_dbTable_batch(self.items_to_add, item)

    @classmethod
    def flush_dbTable_batch(cls, dbTable_batch:List[DbItem], dbTable:DbTable):
        """
        Flush the DBItems of the given dbTable_batch to the given dbTable
        """
        num_items = len(dbTable_batch)
        if num_items == 0:
            logger.info("flush of empty dbTable_batch ignored")
            return
        try:
            logger.info("flushing %d items from dbTable_batch", num_items)
            with dbTable.batch_writer() as batch:
                for item in dbTable_batch:

                    print(f"putting item\n{json.dumps(item, indent=2)}")
                    batch.put_item(Item=item)

            dbTable_batch = []
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in flush_dbTable_batch with %d items for dbTable: %s: %s",
                len(dbTable_batch), dbTable.table_name, {error})
            logger.info()
            raise

    def flush_self_batch(self):
        """
        Flush the DBItems of the given items_to_add list of this YouTubeTable object
        """
        YouTubeTable.flush_dbTable_batch(self.items_to_add, self.dbTable)


    def get_self_item(self, key: DbItem) -> DbItem:
        """
        Retrieve a DbItem from the YouTubeTable.

        :param key: A dictionary representing the key of the item to retrieve.
        :return: The retrieved item.
        """
        try:
            response = self.dbTable.get_item(Key=key)
            return response.get('Item')
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in get_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def update_self_item(self, key: Dict[str,Any], update_expression: str, expression_attribute_values: Dict[str,Any]):
        """
        Update an item in the YouTubeTable.

        :param key: A dictionary representing the key of the item to update.
        :param update_expression: An update expression string.
        :param expression_attrerroribute_values: A dictionary of attribute values.
        """
        try:
            self.dbTable.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in update_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def delete_self_item(self, key: Dict[str,Any]):
        """
        Delete an item in the YouTubeTable.

        :param key: A dictionary representing the key of the item to delete.
        """
        try:
            self.dbTable.delete_item(Key=key)
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in delete_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def scan_dbTable(self, dbTable:DbTable) -> List[DbItem]:
        """
        Scan the entire DbTable.

        :return: A list of all DynamoDbItems in the DbTable.
        """
        try:
            response = dbTable.scan()
            return response.get('Items', [])
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in scan_dbTable %s: %s", dbTable.table_name, {error})
            raise

    def scan_self_table(self) -> List[DbItem]:
        return YouTubeTable.scan_dbTable(self.dbTable)

    @classmethod
    def count_dbTable_items(cls, dbTable:DbTable) -> int:
        """
        return the number of items in this DbTable.

        :return: An integer count of the number of items in this dbTable.
        """
        try:
            total_items = 0
            response = dbTable.scan(Select='COUNT')

            while 'LastEvaluatedKey' in response:
                total_items += response['Count']
                response = dbTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], Select='COUNT')
            else: # pylint: disable=W0120 # Else clause on a loop without a break statement
                total_items += response['Count']

            return total_items
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in scan_dbTable %s: %s", dbTable.table_name, {error})
            raise

    def count_self_table_items(self) -> int:
        return YouTubeTable.count_dbTable_items(self.dbTable)

    def query_self_table(self, key_condition_expression: str, expression_attribute_values: Dict[str,Any]) -> List[DbItem]:
        """
        Query this YouTubeTable with a specific condition.

        :param key_condition_expression: A condition expression string.
        :param expression_attribute_values: A dictionary of attribute values.
        :return: A list of items that match the query.
        """
        if not self.dbTable_exists():
            logger.warning("query_table ignored: table %s does not exist", self.table_name)
            return []
        try:
            response = self.dbTable.query(
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            if response:
                return response.get('Items', [])

            logger.warning("query on table: %s yielded zero responses", self.table_name)
            return []

        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in query_table %s: %s", self.table_name, {error})
            raise

    def delete_self_dbTable(self):
        """ delete this object's dbTable """
        if not self.dbTable_exists():
            logger.warning("delete_dbTable ignored: table %s does not exist", self.table_name)
            return
        try:
            self.dbTable.delete()
            # Wait until the table is deleted
            self.dbTable.meta.client.get_waiter('table_not_exists').wait(TableName=self.table_name)
            logger.info("Table %s has been deleted.", self.table_name)
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in delete table %s: %s", self.table_name, {error})
            raise

    @classmethod
    def dump_dbTable_to_json(cls, dbTable_name:str, json_file_path:str, json_config_path:str=None):
        """ find a dbTable by name and dump its contents and its config to the given json_file_paths
            if json_config_path is not defined then create it from the json_file_path as
            if json_file_path="x/y/z/dump.json" then json_config_path="x/y/z/dump-config.json

        """
        # default the json_config_path from the json_file_path
        # if json_file_path="x/y/z/dump.json" then json_config_path="x/y/z/dump-config.json
        if not json_config_path:
            json_config_path = json_file_path.replace(".json", "-config.json")

        # error if dbTable not found by name
        dbTable = cls.find_dbTable_by_name(dbTable_name)
        if not dbTable:
            raise RuntimeError("dbTable with dbTable:%s not found", dbTable_name)

        # error if dbTable config extraction failed
        dTable_config = cls.extract_dbTable_config(tbTable_name)
        if not dbTable_config:
            raise RuntimeError("dbTable_config for dbTable:%s not loaded", dbTable_name)

        # dump the config file
        logger.info("dumping config for dbTable:%s to %s", dbTable_name, json_config_path)
        DynamoDbJsonUItils.dump_json_file(dTable_config,json_config_path)

        # dump the data
        response = dbTable.scan()
        data = response['Items']
        logger.info("dumping %d items from table:%s to %s", len(data), dbTable_name, json_file_path)
        DynamoDbJsonUtils.dump_json_file(data, json_file_path, json_config_path)

        logger.info("table:%s dumped %d items to %s", dbTable_name, len(data), json_file_path)

    @classmethod
    def load_dbTable_from_json_with_copy(cls, dbTable_name:str, json_file_path:str, json_config_path:str=None):
        """ find a dbTable by name, create a new dbTable if needed
            if the dbTable does not exist, and if json_config_path is
            not defined then create it from the json_file_path as
            "x/y/z/dump.json" to "x/y/z/dump-config.json
            then use them both to create the new dbTable.
            and load the contents of the given json_file_path into the dbTable
        """
        # default the json_config_path from the json_file_path
        # if json_file_path="x/y/z/dump.json" then json_config_path="x/y/z/dump-config.json
        if not json_config_path:
            json_config_path = json_file_path.replace(".json", "-config.json")

        dbTable = cls.find_dbTable_by_name(dbTable_name)
        if not dbTable:
            logger.info("loading config for dbTable:%s from %s", dbTable_name, json_config_path)
            dbTable_config = DynamoDbJsonUItils.load_json_file(json_config_path)
            dbTable_config['TableName'] = dbTable_name
            dBTable = cls.create_dbTable(dbTable_config)
            logger.info("created new dbTable with dbTable_config: %s", json.dumps(dbTable_config, indent=2) )

        original_count = cls.count_dbTable_items(dbTable)
        data = DynamoDbJsonUtils.load_json_file(json_file_path)
        load_count = len(data)
        logger.info("loading %d items from %s into dbTable:%s", load_count, json_file_path, dbTable_name)
        dbTable_batch = []
        for item in data:
            cls.add_item_to_dbTable_batch(item, dbTable_batch)
        cls.flush_dbTable_batch(dbTable_batch, dbTable)
        final_count = cls.count_dbTable_items(dbTable)
        logger.info("dbTable:%s original_count:%d loaded_count:%d final_count:%d", dbTable_name, original_count, final_count)
