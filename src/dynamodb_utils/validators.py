import json
from json import JSONDecodeError
from dateutil import parser

from dynamodb_utils.dbtypes import *

class DynamoDbValidators:

    @staticmethod
    def is_valid_iso8601_string(date_string:str) -> bool:
        try:
            parser.isoparse(date_string)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_dbItem(item:DbItem) -> bool:
        """
        Validate if the given item is a valid DynamoDB item.

        Args:
            item (Dict[str, Any]): The item to validate.

        Returns:
            bool: True if the item is valid, False otherwise.
        """
        required_keys = ["response_id"]  # Replace with your required keys
        for key in required_keys:
            if key not in item:
                return False
        return True
    

if __name__ == "__main__":
    pass