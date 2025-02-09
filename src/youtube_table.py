# pylint: disable=C0103 # Invalid name

import json
import logging
import os
from typing import Dict, Any, List

import boto3
from boto3.resources.base import ServiceResource

from dynamodb_utils import DynamoDbItemPreProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DbItem = Dict[str, Any]
DbTable = ServiceResource

class YouTubeTableException(Exception):
    pass

class YouTubeTable:
    def __init__(self, table_config: Dict[str, str], dynamodb_resource: ServiceResource = None):

        try:
            self.dynamodb_url = os.getenv('DYNAMODB_URL')
            self.dynamodb_client = boto3.client('dynamodb', endpoint_url=self.dynamodb_url)
            self.dynamodb_resource = dynamodb_resource or boto3.resource('dynamodb', endpoint_url=self.dynamodb_url)
            self.table_config = table_config
            self.table_name = self.table_config['TableName']
            self.dbTable = self.find_dbTable_by_name(self.table_name)

            if not self.dbTable:
                self.dbTable = self.create_dbTable()

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

    def get_table_name(self) -> str:
        return self.table_name

    def get_preprocessed_item(self, item: DbItem) -> DbItem:
        return self.item_preprocessor.get_preprocessed_item(item)

    def create_dbTable(self) -> DbTable:
        """
        Create the DynamoDb table with the loaded configuration.

        The configuration should include:
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
            new_dbTable = self.dynamodb_resource.create_dbTable(**self.table_config)
            return new_dbTable
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in create_dbTable table: %s: %s", self.table_name, {error})
            raise

    def find_dbTable_by_name(self, table_name: str) -> DbTable:
        """
        Find a DynamoDb table by its name, or return None

        :param table_name: The name of the table to check for existence.
        :return: The table if it exists, None otherwise.
        """
        found_dbTable = None
        try:
            # Attempt to describe the table. If this succeeds, the table exists.
            found_dbTable = self.dynamodb_resource.Table(table_name)
            # Check if we can describe the table to confirm it's accessible
            self.dynamodb_client.describe_table(TableName=table_name)
        except self.dynamodb_client.exceptions.ResourceNotFoundException:
            # If the table doesn't exist, we'll get this exception.
            found_dbTable = None
        except boto3.exceptions.Boto3Error as error:
            # Catch other exceptions and log them for debugging.
            print(f"An error occurred while checking for table {table_name}: {error}")
            found_dbTable = None

        return found_dbTable

    def add_item(self, item: DbItem):
        """
        Add a new DbItem to the YouTubeTable.

        :param item: A dictionary representing the item to add.
        """
        try:
            self.dbTable.put_item(Item=item)
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in add_item for table: %s: %s", self.table_name, {error})
            raise

    def add_item_to_batch(self, item: DbItem):
        """
        Add an item to the batch.

        :param item: A dictionary representing the item to add.
        """
        try:
            self.items_to_add.append(item)
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in add_item_to_batch for table: %s: %s", self.table_name, {error})
            raise

    def reset_batch(self):
        self.items_to_add = []

    def flush_batch(self):
        """
        Flush the batch of items to the YouTubeTable.
        """
        num_items = len(self.items_to_add)
        if num_items == 0:
            logger.info("flush of empty batch ignored")
            return
        try:
            logger.info("flushing %d items from batch", num_items)
            with self.dbTable.batch_writer() as batch:
                for item in self.items_to_add:

                    print(f"putting item\n{json.dumps(item, indent=2)}")
                    batch.put_item(Item=item)

            self.reset_batch()
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in flush_batch with %d items for table: %s: %s",
                len(self.items_to_add), self.table_name, {error})
            logger.info()
            raise

    def get_item(self, key: DbItem) -> DbItem:
        """
        Retrieve a DbItem from the YouTubeTable.

        :param key: A dictionary representing the key of the item to retrieve.
        :return: The retrieved item.
        """
        try:
            response = self.dbTable.get_item(Key=key)
            return response.get('Item')
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in get_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def update_item(self, key: Dict[str,Any], update_expression: str, expression_attribute_values: Dict[str,Any]):
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
            logger.eror("An error occurred in update_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def delete_item(self, key: Dict[str,Any]):
        """
        Delete an item in the YouTubeTable.

        :param key: A dictionary representing the key of the item to delete.
        """
        try:
            self.dbTable.delete_item(Key=key)
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in delete_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def scan_table(self) -> List[DbItem]:
        """
        Scan the entire YouTubeTable.

        :return: A list of all DynamoDbItems in the table.
        """
        try:
            response = self.dbTable.scan()
            return response.get('Items', [])
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in scan_table %s: %s", self.table_name, {error})
            raise

    def count_items(self) -> int:
        """
        return the number of items in this YouTubeTable.

        :return: An integer count of the number of items in the table.
        """
        try:
            total_items = 0
            response = self.dbTable.scan(Select='COUNT')

            while 'LastEvaluatedKey' in response:
                total_items += response['Count']
                response = self.dbTable.scan(ExclusiveStartKey=response['LastEvaluatedKey'], Select='COUNT')
            else: # pylint: disable=W0120 # Else clause on a loop without a break statement
                total_items += response['Count']

            return total_items
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in scan_table %s: %s", self.table_name, {error})
            raise

    def query_table(self, key_condition_expression: str, expression_attribute_values: Dict[str,Any]) -> List[DbItem]:
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
            logger.eror("An error occurred in query_table %s: %s", self.table_name, {error})
            raise

    def delete_dbTable(self):
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
            logger.eror("An error occurred in delete table %s: %s", self.table_name, {error})
            raise
