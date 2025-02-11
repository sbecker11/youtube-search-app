import json
import logging
from typing import Dict, Set, Any
from decimal import Decimal
from dateutil import parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDbItemPreProcessor:
    def __init__(self, the_table_config, attribute_name_prefix=None):
        self.key_prefixes = {}
        self.type_mappings = {}
        self.table_config = the_table_config
        self.table_name = the_table_config["TableName"]

        # Default for table_name "Responses" is "response."
        # Default for table_name "Snippets" is "snippet."
        # Default for table_name "Parties" is "party."
        if not attribute_name_prefix:
            attribute_name_prefix = DynamoDbStringUtils.singularize(self.table_name.lower()) + '.'
        self.attribute_name_prefix = attribute_name_prefix

        for attr in self.table_config['AttributeDefinitions']:
            if attr['AttributeName'].startswith(self.attribute_name_prefix):
                original_name = attr['AttributeName'][len(self.attribute_name_prefix):]
                self.key_prefixes[original_name] = self.attribute_name_prefix
                self.type_mappings[original_name] = attr['AttributeType']

    def get_preprocessed_item(self, raw_item):
        pre_processed_item = {}
        for attr_name, value in raw_item.items():
            if attr_name in self.key_prefixes:
                prefixed_name = f"{self.key_prefixes[attr_name]}{attr_name}"
                type_mapping = self.type_mappings[attr_name]
                if type_mapping:
                    try:
                        if type_mapping == 'S':
                            pre_processed_item[prefixed_name] = self.to_string(value)
                        elif type_mapping == 'N':
                            pre_processed_item[prefixed_name] = self.to_number(value)
                        elif type_mapping == 'B':
                            pre_processed_item[prefixed_name] = self.to_boolean(value)
                        else:
                            raise ValueError(f"type_mapping:{type_mapping} not supported")
                    except ValueError as error:
                        logger.error("type_mapping:%s for value:%s error: %s", type_mapping, value, error)
            else:
                # Non-key attributes remain unchanged
                pre_processed_item[attr_name] = value
        return pre_processed_item

    def to_number(self, value):
        try:
            # Try to convert to integer
            return int(value)
        except ValueError:
            try:
                # If integer conversion fails, try to convert to float
                return float(value)
            except ValueError as exc:
                # If both conversions fail, raise an error
                raise ValueError(f"Cannot convert {value} to a number") from exc

    def to_string(self, value):
        return str(value)

    def to_boolean(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes']:
                return True
            elif value.lower() in ['false', '0', 'no']:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        raise ValueError(f"Cannot convert {value} to a boolean")

    @staticmethod
    def example_usage(a_snippets_table_config):
        # Usage
        pre_processor = DynamoDbItemPreProcessor(a_snippets_table_config, attribute_name_prefix="snippet.")
        raw_item = {
            'channelId': 'UCRAu2aXcH-B5h9SREfyhXuA',
            'publishedAt': '2025-02-05T11:35:37Z',
            'title': 'Example Title',
            'description': 'Example Description'
        }

        processed_rows = []
        rows = [raw_item]  # Assuming rows is a list of raw items
        for raw_item in rows:
            print(f"raw_item: {raw_item}")
            pre_processed_item = pre_processor.get_preprocessed_item(raw_item)
            print(f"pre_processed_item: {pre_processed_item}")
        processed_rows.append(pre_processed_item)

if __name__ == "__main__":

    # Example table configuration
    snippets_table_config = {
        "TableName": "Snippets",
        "KeySchema": [
            {
                "AttributeName": "snippet.channelId",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "snippet.publishedAt",
                "KeyType": "RANGE"
            }
        ],
        "AttributeDefinitions": [
            {
                "AttributeName": "snippet.channelId",
                "AttributeType": "S"
            },
            {
                "AttributeName": "snippet.publishedAt",
                "AttributeType": "S"
            }
        ],
        "ProvisionedThroughput": {
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        }
    }

    DynamoDbItemPreProcessor.example_usage(snippets_table_config)
