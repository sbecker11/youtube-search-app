import json
import logging
from typing import Dict, Set, Any
from decimal import Decimal
from dateutil import parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDbStringUtils:

    @staticmethod
    def singularize(word):
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

