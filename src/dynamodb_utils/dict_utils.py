import json
import logging
from typing import Dict, Set, Any
from decimal import Decimal
from dateutil import parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDbDictUtils:

    @staticmethod
    def flatten_dict(current_dict:Dict, parent_key:str='', sep:str='.', expected_key_set:Set[str]=None) -> Dict[str,str]:
        if expected_key_set is None:
            expected_key_set = set()

        items = []
        for key, val in current_dict.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(val, dict):
                if expected_key_set is not None:
                    if key in expected_key_set:
                        expected_key_set.remove(key)
                if isinstance(val, Decimal):
                    val = float(val)
                elif isinstance(val, str):
                    try:
                        val = parser.parse(val)
                    except (ValueError, TypeError): 
                        pass
                items.extend(DynamoDbDictUtils.flatten_dict(current_dict=val, parent_key=new_key, sep=sep, expected_key_set=expected_key_set).items())
            else:
                items.append((new_key, val))

        for key in expected_key_set:
            full_key = f"{parent_key}{sep}{key}" if parent_key else key
            if full_key not in [item[0] for item in items]:
                items.append((full_key, None))

        return dict(items)

    @staticmethod
    def unflatten_dict(flat_dict: Dict, sep='.') -> Dict[str,Any]:
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


if __name__ == "__main__":

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
    flattened = DynamoDbDictUtils.flatten_dict(current_dict=thumbnails, parent_key='thumbnails', expected_key_set=thumbnail_key_set)

    unflattened = DynamoDbDictUtils.unflatten_dict(flattened)

    original_str = json.dumps(thumbnails,indent=2)
    unflattened_str = json.dumps(unflattened,indent=2)
    if unflattened_str == original_str:
        print("SUCCESS")
    else:
        print("FAILURE")

