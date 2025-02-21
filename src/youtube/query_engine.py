# pylint: disable=W1203 # Use lazy % formatting in logging functions
# pylint: disable=E1101 # Instance has no 'xxx' member
# pylint: disable=all   # another option

import os
from datetime import datetime
import logging

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube.youtube_storage import YouTubeStorage

# Load .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryEngineException(Exception):
    pass
class QueryEngine:
    """ Submits queries to YouTube metadata API
        and stores each query request and its
        query response details to YouTubeStorage.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # Only pass the class, no additional args
        return cls._instance

    @classmethod
    def get_singleton(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):

        if not hasattr(self, 'initialized'):
            self.initialized = False  # singleton logic to ensure that heavy initialization is done only once
        elif self.initialized:
            return

        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_api_key:
            raise RuntimeError("QueryEngine YOUTUBE_API_KEY is undefined")

        self.youtube_api_client = build('youtube', 'v3', developerKey=youtube_api_key)
        logger.info("the QueryEngine instance is now initialized with youtube_api_client")

        self.youtube_storage = YouTubeStorage.get_singleton()
        logger.info("the QueryEngine instance is now initialized with the YouTubeStorage instance")

        self.initialized = True  # Flag to show heavy initialization has been done

    def search(self, subject: str):
        request_params = {
            "part": "snippet",
            "q": subject,
            "type": "video",
            "maxResults": 25
        }
        try:
            params_string = self.stringify_params(**request_params)
            logger.info(f"request submitted with params: {params_string}")
            youtube_request = self.youtube_api_client.search().list(**request_params)
            youtube_response = youtube_request.execute()
            logger.info("response received")

        except HttpError as error:
            logger.error(f"An HTTP error occurred: {error}")
            raise QueryEngineException(error)

        query_request = {
            'subject': subject,
            'requestSubmittedAt': datetime.utcnow().isoformat(),
            **request_params
        }
        query_response = youtube_response

        logger.info("storing query request and response")
        self.youtube_storage.add_query_request_and_response(query_request, query_response)

    def stringify_params(self,**params):
        """ create a dictionary and then a string given a set of params """
        stringfied = ', '.join(f"{key}={value}" for key, value in params.items())
        print(f"stringfied: {stringfied}")
        return stringfied
