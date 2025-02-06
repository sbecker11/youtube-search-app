import os
import json
from typing import Dict
import boto3

class YouTubeTableException(Exception):
    pass

class YouTubeTable:
    def __init__(self, config:Dict[str,str]):
        try:
            self.dynamodb_url = os.getenv('DYNAMODB_URL')
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=self.dynamodb_url)
            self.config = config
            self.table_name = self.config['TableName']
            config_args = {k: v for k, v in config.items() if k != 'TableName'}
            self.table = self.dynamodb.Table(self.table_name, **config_args)
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
            self.table = self.dynamodb.create_table(**self.config)
        except Exception as error:
            print(f"Error creating table: {error}")
            raise

    def add_item(self, item):
        """
        Add a new item to the YouTubeTable.

        :param item: A dictionary representing the item to add.
        """
        try:
            self.table.put_item(Item=item)
        except Exception as error:
            print(f"Error adding item: {error}")
            raise

    def add_item_to_batch(self, item):
        """
        Add an item to the batch.

        :param item: A dictionary representing the item to add.
        """
        try:
            self.items_to_add.append(item)
        except Exception as error:
            print(f"Error adding item to batch: {error}")
            raise

    def reset_batch(self):
        self.items_to_add = []

    def flush_batch(self):
        """
        Flush the batch of items to the YouTubeTable.
        """
        try:
            with self.table.batch_writer() as batch:
                for item in self.items_to_add:
                    batch.put_item(Item=item)
            self.reset_batch()
        except Exception as error:
            print(f"Error flushing batch: {error}")
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
        except Exception as error:
            print(f"Error getting item: {error}")
            raise

    def update_item(self, key, update_expression, expression_attribute_values):
        """
        Update an item in the YouTubeTable.

        :param key: A dictionary representing the key of the item to update.
        :param update_expression: An update expression string.
        :param expression_attribute_values: A dictionary of attribute values.
        """
        try:
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
        except Exception as error:
            print(f"Error updating item: {error}")
            raise

    def delete_item(self, key):
        """
        Delete an item from the YouTubeTable.

        :param key: A dictionary representing the key of the item to delete.
        """
        try:
            self.table.delete_item(Key=key)
        except Exception as error:
            print(f"Error deleting item: {error}")
            raise

    def scan_table(self):
        """
        Scan the entire YouTubeTable.

        :return: A list of all items in the table.
        """
        try:
            response = self.table.scan()
            return response.get('Items', [])
        except Exception as error:
            print(f"Error scanning table: {error}")
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
        except Exception as error:
            print(f"Error querying table: {error}")
            raise
