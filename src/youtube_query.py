# pylint: disable=W1203 # Use lazy % formatting in logging functions
# pylint: disable=E1101 # Instance has no 'xxx' member
# pylint: disable=all   # another option

import os
from datetime import datetime
import logging

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube_storage import YouTubeStorage

# Load .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeQueryException(Exception):
    pass

class YouTubeQuery:
    """ Submits queries to YouTube metadata API
        and stores each query request and its
        query response details to YouTubeStorage.
    """
    def __init__(self):
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        self.youtube_storage = YouTubeStorage.get_singleton()

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
            youtube_request = self.youtube.search().list(**request_params)
            youtube_response = youtube_request.execute()
            logger.info("response received")

        except HttpError as error:
            logger.error(f"An HTTP error occurred: {error}")
            raise YouTubeQueryException(error)

        youtube_query = {
            'subject': subject,
            'requestSubmittedAt': datetime.utcnow().isoformat(),
            **request_params
        }

        logger.info("storing query response")
        self.youtube_storage.save_query_response(youtube_query, youtube_response)
        logger.info("query response stored")

    def stringify_params(self,**params):
        """ create a dictionary and then a string given a set of params """
        stringfied = ', '.join(f"{key}={value}" for key, value in params.items())
        print(f"stringfied: {stringfied}")
        return stringfied
