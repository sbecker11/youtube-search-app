# pylint: disable=C0103 # Invalid name

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

import boto3
import botocore
from boto3.resources.base import ServiceResource
from botocore.exceptions import ClientError

from dynamodb_utils.item_utils import DynamoDbItemPreProcessor
from dynamodb_utils.filter_utils import DynamoDbFilterUtils
from dynamodb_utils.json_utils import DynamoDbJsonUtils
from dynamodb_utils.table_utils import DynamoDbTableUtils
from dynamodb_utils.dict_utils import DynamoDbDictUtils
from dynamodb_utils.validators import DynamoDbValidators
from dynamodb_utils.dbtypes import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            # save table config and name
            self.table_config = table_config
            self.table_name = self.table_config['TableName']

            # check if the table already exists
            self.dbTable = YouTubeTable.find_dbTable_by_name(self.table_name)

            # if the table does not exist, create it
            if not self.dbTable:
                self.dbTable = YouTubeTable.create_dbTable(self.table_config)

            # create a preprocessor for the items
            self.item_preprocessor = DynamoDbItemPreProcessor(self.table_config)

        except boto3.exceptions.Boto3Error as error:
            logger.error(f"Error initializing DynamoDb resource: {error}")
            raise
        except FileNotFoundError as error:
            logger.error(f"Configuration file not found: {error}")
            raise
        except json.JSONDecodeError as error:
            logger.error(f"Error decoding JSON configuration: {error}")
            raise

        logger.info("YouTubeTable '%s' successfully initialized with dbTable", self.table_name)

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
            logger.error(f"Error checking if dynamoDb table exists: {error}")
            raise
    
    def get_table_config(self):
        logger.info("self.table_name: %s", self.table_name)
        return YouTubeTable.get_dbTable_config(self.table_name)

    @classmethod
    def get_dbTable_config(cls,table_name):
        logger.info("table_name: %s", table_name)
        config_prop_names = ['TableName', 'KeySchema', 'AttributeDefinitions', 'ProvisionedThroughput']
        table_description = YouTubeTable.dynamodb_client.describe_table(TableName=table_name)
        if not table_description:
            raise YouTubeTableException(f"Table {table_name} does not exist.")
        configs = []
        for prop_name in config_prop_names:
            prop_value = table_description['Table'][prop_name]
            prop_text = DynamoDbJsonUtils.json_dumps(prop_value,indent=4)
            configs.append(f" \"{prop_name}\": {prop_text}")
        config_text = "{\n" + ",\n".join(configs) + "\n}"
        dbTable_config = json.loads(config_text)
        return dbTable_config

    def get_table_name(self) -> str:
        return self.table_name

    def get_preprocessed_item(self, item: DbItem) -> DbItem:
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
            logger.error(f"An error occurred while checking for table {table_name}: {error}")
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
            logger.error("An error occurred in get_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def update_item(self, key: Dict[str,Any], update_expression: str, expression_attribute_values: Dict[str,Any]):
        """
        Update an item in the dbTable of this YouTubeTable.

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

    def delete_item(self, key: Dict[str,Any]):
        """
        Delete an item in the dbTable of this YouTubeTable.

        :param key: A dictionary representing the key of the item to delete.
        """
        try:
            self.dbTable.delete_item(Key=key)
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in delete_item with key:%s for table: %s: %s", key, self.table_name, {error})
            raise

    def scan_table(self) -> List[DbItem]:
        """
        Return a list of all DbItems of the dbTable of this YouTubeTable

        Returns:
            List[DbItem]: all rows of the dbTable of this YouTubeTable
        """
        return self.scan_dbTable(self.dbTable)

    def delete_dbTable(self, dbTable):
        if not dbTable.exists():
            logger.warning("delete_dbTable ignored: table %s does not exist", dbTable.table_name)
            return
        try:
            self.dbTable.delete()
            # Wait until the table is deleted
            self.dbTable.meta.client.get_waiter('table_not_exists').wait(TableName=self.table_name)
            logger.info("Table %s has been deleted.", self.table_name)
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in delete table %s: %s", self.table_name, {error})
            raise

    def scan_items(self, filter_expression: Optional[str] = None, expression_attribute_values: Optional[Dict[str, Any]] = None) -> List[DbItem]:
        """
        Scan the dbTable of this YouTubeTable with optional filter expression.

        :param filter_expression: An optional filter expression.
        :param expression_attribute_values: An optional dictionary of attribute values.
        :return: A list of filtered DbItems.
        """
        return self.scan_dbTable(self.dbTable, filter_expression, expression_attribute_values)

    def scan_dbTable(self, dbTable:DbTable, filter_expression: Optional[str] = None, expression_attribute_values: Optional[Dict[str, Any]] = None) -> List[DbItem]:
        """
        Scan the entire DbTable.

        :return: A list of all DynamoDbItems in the DbTable that match the given filter expression and attributes.
        """
        try:
            if filter_expression and expression_attribute_values:
                response = dbTable.scan(filter_expression=filter_expression, expression_attribute_values=expression_attribute_values)
            else:
                response = dbTable.scan()
            return response.get('Items', [])
        except boto3.exceptions.Boto3Error as error:
            logger.error("An error occurred in scan_dbTable %s: %s", dbTable.table_name, {error})
            raise

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

    def load_dbItems(self, dbItems:List[DbItem], idempotent:bool=True):
        """
        Load a list of DbItems into the dbTable of this YouTubeTable.

        :param dbItems: A list of dictionaries representing the items to load.
        :param idempotent: If True, use conditional writes to ensure items do not already exist.
        """
        YouTubeTable.put_dbTable_items(self.dbTable, dbItems, idempotent)

    def add_item(self, item:DbItem, idempotent=True):
        YouTubeTable.put_dbTable_items(self.dbTable, [item], idempotent)
        """ convenience function """

    def add_items(self, items:List[DbItem], idempotent=True):
        YouTubeTable.put_dbTable_items(self.dbTable, items, idempotent)
        """ convenience function """

    @classmethod
    def put_dbTable_items(cls, dbTable:DbTable, items:List[DbItem], idempotent:bool=False) -> List[DbItem]:
        """
        If the `idempotent` flag is set to True, the method ensures that items are only added
        if they do not already exist in the table.
        Args:
            dbTable: DbTable: used to create a batch_writer
            dbItems: List[DbItem] : the items to be stored to the table
            idempotent (bool): If True, use conditional writes to ensure items do not already exist.
            if False, use batch_writer for bulk writes.
        Raises:
            ClientError: If there is an error during any single put item, it will be reported
            but the function will continue and attempt to store the next item.
        Notes:
            - If the table already exists and idempotent is set to true
              then items will only be inserted if the item's primary key
              already exists in the table
        """
        logger.info(f"dbTable.type:{type(dbTable)} dbTable.value:{dbTable}")
        logger.info(f"item.type:{type(items)} item.value:{items}")
        logger.info(f"idempotent.type:{type(idempotent)} idempotent.value:{idempotent}")

        successful_writes = []
        failed_writes = []
        
        if idempotent:
            # Handle idempotent writes with individual put_item calls
            for dbItem in items:
                if DynamoDbValidators.is_valid_dbItem(dbItem):  # Assuming this is your validator
                    try:
                        # Use regular put_item with ConditionExpression for idempotency
                        dbTable.put_item(
                            Item=dbItem,
                            ConditionExpression='attribute_not_exists(#pk)',
                            ExpressionAttributeNames={'#pk': 'id'}  # Replace 'id' with your partition key
                        )
                        successful_writes.append(dbItem)
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                            logger.info(f"Item with id {dbItem.get('id')} already exists, skipping.")
                        else:
                            logger.error(f"Error writing item {dbItem}: {e}")
                            failed_writes.append(dbItem)
        else:
            # Use batch_writer for non-idempotent bulk writes
            with dbTable.batch_writer() as dbBatch:
                for dbItem in items:
                    if DynamoDbValidators.is_valid_dbItem(dbItem):
                        try:
                            dbBatch.put_item(Item=dbItem)
                            successful_writes.append(dbItem)
                        except Exception as e:
                            logger.error(f"Error writing item {dbItem}: {e}")
                            failed_writes.append(dbItem)
        num_items_total = len(items)
        num_items_successful = len(successful_writes)
        num_items_failed = len(failed_writes)
        logger.info("num items total: %d num items successful: %d num items failed:%d", num_items_total, num_items_successful, num_items_failed)
        return successful_writes




if __name__ == "__main__":
    logger.info("Hello there.")