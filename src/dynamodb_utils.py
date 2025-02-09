# pylint: disable=R0903 # Too few public methods

import json
import logging
from typing import Dict, Set, Any
from dateutil import parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDbValidators:

    @classmethod
    def is_valid_iso8601_string(cls, date_string:str) -> bool:
        try:
            parser.isoparse(date_string)
            return True
        except ValueError:
            return False

class DynamoDbStringUtils:

    @classmethod
    def singularize(cls, word):
        """
        Convert a plural English word to its singular form.

        Args:
            word (str): The plural word to convert

        Returns:
            str: The singular form of the word
        """
        if word.endswith('ies'):
            return word[:-3] + 'y'
        if word.endswith('s'):
            return word[:-1]
        return word


class DynamoDbJsonUtils:

    @classmethod
    def load_json_file(cls, json_file_path: str) -> Dict[str, Any]:
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error("JSON file not found at %s:", json_file_path)
            return {}  # Return empty dict instead of raising an exception
        except json.JSONDecodeError as error:
            logger.error("Error decoding JSON file at %s: %s", json_file_path, error)
            return {}

class DynamoDbDictUtils:

    @classmethod
    def flatten_dict(cls, current_dict:Dict, parent_key:str='', sep:str='.', expected_key_set:Set[str]=None) -> Dict[str,str]:
        if expected_key_set is None:
            expected_key_set = set()

        items = []
        for key, val in current_dict.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(val, dict):
                expected_key_set.update(val.keys())
                items.extend(cls.flatten_dict(current_dict=val, parent_key=new_key, sep=sep, expected_key_set=expected_key_set).items())
            else:
                items.append((new_key, val))

        for key in expected_key_set:
            full_key = f"{parent_key}{sep}{key}" if parent_key else key
            if full_key not in [item[0] for item in items]:
                items.append((full_key, None))

        return dict(items)

    @classmethod
    def unflatten_dict(cls, flat_dict: Dict, sep='.') -> Dict[str,Any]:
        """ takes a flattened dict and converts it back to a multi-level dict hiearchy """
        result = {}
        for key, value in flat_dict.items():
            parts = key.split(sep)
            current_level = result
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            current_level[parts[-1]] = value
        return result

    @classmethod
    def test_dict_utils(cls):
        thumbnails = {
            "default": {
                "url": "https://google.com?id=1234",
                "width": 1024,
                "height": 820
            },
            "maxres": {
                "url": "https://google.com?id=1234&maxres=true",
                "width": 1920,
                "height": 1080
            }
        }
        thumbnail_key_set = {"url", "width", "height"}
        flattened = cls.flatten_dict(current_dict=thumbnails, parent_key='thumbnails', expected_key_set=thumbnail_key_set)

        unflattened = cls.unflatten_dict(flattened)

        original_str = json.dumps(thumbnails,indent=2)
        unflattened_str = json.dumps(unflattened,indent=2)
        if unflattened_str == original_str:
            print("SUCCESS")
        else:
            print("FAILURE")


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

    def to_number(self,value):
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

    @classmethod
    def example_usage(cls, a_snippets_table_config):
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
