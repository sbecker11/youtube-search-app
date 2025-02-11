import json
import logging
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDbJsonUtils:
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return int(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, list):
                return [self.default(item) for item in obj]
            if isinstance(obj, dict):
                return {key: self.default(value) for key, value in obj.items()}
            return super(DynamoDbJsonUtils.CustomEncoder, self).default(obj)

    @staticmethod
    def load_json_file(json_file_path: str) -> Dict[str, Any]:
        """ returns a json object after removing commented portions or empty dict """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                return data
        except FileNotFoundError:
            logger.error("JSON file not found at %s:", json_file_path)
            return {}
        except json.JSONDecodeError as error:
            logger.error("Error decoding JSON file at %s: %s", json_file_path, error)
            return {}

    @staticmethod
    def json_dumps(data: Any, indent=4) -> str:
        if not data:
            return ""
        return json.dumps(data, indent=indent, cls=DynamoDbJsonUtils.CustomEncoder)

    @staticmethod
    def dump_json_file(data: Dict[str, Any], json_file_path: str):
        """ dumps a json object to a file using CustomEncoder """
        try:
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, cls=DynamoDbJsonUtils.CustomEncoder)
            logger.info("Data successfully dumped to %s", json_file_path)
        except Exception as error:
            logger.error("Error dumping JSON file at %s: %s", json_file_path, error)

if __name__ == "__main__":
    pass