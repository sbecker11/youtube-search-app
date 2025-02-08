import json
import logging
import os
from typing import Dict

import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class YouTubeTableException(Exception):
    pass

class YouTubeTable:
    def __init__(self, config:Dict[str,str]):

        try:
            self.dynamodb_url = os.getenv('DYNAMODB_URL')
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=self.dynamodb_url)
            self.config = config
            self.table_name = self.config['TableName']

            self.table = self.find_table_by_name(self.table_name)

            if not self.table:
                self.table = self.create_table()

            # initialize the batch list
            self.items_to_add = []

        except boto3.exceptions.Boto3Error as error:
            print(f"Error initializing DynamoDB resource: {error}")
            raise
        except FileNotFoundError as error:
            print(f"Configuration file not found: {error}")
            raise
        except json.JSONDecodeError as error:
            print(f"Error decoding JSON configuration: {error}")
            raise

        logger.info("YouTubeTable '%s' successfully initialized", self.table_name)

    def table_exists(self):
        """
        Check if the table already exists.

        :return: True if the table exists, False otherwise.
        """
        try:
            self.dynamodb.meta.client.describe_table(TableName=self.table_name)
            return True
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            return False
        except Exception as error:
            print(f"Error checking if table exists: {error}")
            raise

    def create_table(self):
        """
        Create the DynamoDB table with the loaded configuration.

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
            new_table = self.dynamodb.create_table(**self.config)
            return new_table
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in create_table table: %s: %s", self.table_name, {error})
            raise

    def find_table_by_name(self, table_name):
        """
        Check if a DynamoDB table exists by its name.

        :param table_name: The name of the table to check for existence.
        :return: True if the table exists, False otherwise.
        """
        try:
            # Attempt to describe the table. If this succeeds, the table exists.
            found_table = self.dynamodb.Table(table_name)
            # Check if we can describe the table to confirm it's accessible
            self.dynamodb.meta.client.describe_table(TableName=table_name)
            return found_table
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            # If the table doesn't exist, we'll get this exception.
            return None
        except boto3.exceptions.Boto3Error as error:
            # Catch other exceptions and log them for debugging.
            print(f"An error occurred while checking for table {table_name}: {error}")
            return None

    def add_item(self, item):
        """
        Add a new item to the YouTubeTable.

        :param item: A dictionary representing the item to add.
        """
        try:
            self.table.put_item(Item=item)
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in add_item for table: %s: %s", self.table_name, {error})
            raise

    def add_item_to_batch(self, item):
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
            with self.table.batch_writer() as batch:
                for item in self.items_to_add:

                    print(f"putting item\n{json.dumps(item, indent=2)}")
                    batch.put_item(Item=item)

            self.reset_batch()
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in flush_batch with %d items for table: %s: %s",
                len(self.items_to_add), self.table_name, {error})
            logger.info()
            raise

    def get_item(self, key):
        """
        Retrieve an item from the YouTubeTable.

        :param key: A dictionary representing the key of the item to retrieve.
        :return: The retrieved item.
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in get_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def update_item(self, key, update_expression, expression_attribute_values):
        """
        Update an item in the YouTubeTable.

        :param key: A dictionary representing the key of the item to update.
        :param update_expression: An update expression string.
        :param expression_attrerroribute_values: A dictionary of attribute values.
        """
        try:
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in update_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def delete_item(self, key):
        """
        Delete an item from the YouTubeTable.

        :param key: A dictionary representing the key of the item to delete.
        """
        try:
            self.table.delete_item(Key=key)
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in delete_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def scan_table(self):
        """
        Scan the entire YouTubeTable.

        :return: A list of all items in the table.
        """
        try:
            response = self.table.scan()
            return response.get('Items', [])
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in scan_table %s: %s", self.table_name, {error})
            raise

    def count_items(self) -> int:
        """
        return the number of items in the entire YouTubeTable.

        :return: An integer count of the number of items in the table.
        """
        try:
            total_items = 0
            response = self.table.scan(Select='COUNT')

            while 'LastEvaluatedKey' in response:
                total_items += response['Count']
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'], Select='COUNT')
            else: # pylint: disable=W0120 # Else clause on a loop without a break statement
                total_items += response['Count']

            return total_items
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in scan_table %s: %s", self.table_name, {error})
            raise


    def query_table(self, key_condition_expression, expression_attribute_values):
        """
        Query the YouTubeTable with a specific condition.

        :param key_condition_expression: A condition expression string.
        :param expression_attribute_values: A dictionary of attribute values.
        :return: A list of items that match the query.
        """
        try:
            response = self.table.query(
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            return response.get('Items', [])
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in query_table %s: %s", self.table_name, {error})
            raise



    def delete_table(self):
        try:
            self.table.delete()
            # Wait until the table is deleted
            self.table.meta.client.get_waiter('table_not_exists').wait(TableName=self.table_name)
            logger.info("Table %s has been deleted.", self.table_name)
        except boto3.exceptions.Boto3Error as error:
            logger.eror("An error occurred in delete table %s: %s", self.table_name, {error})
            raise
