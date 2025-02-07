import logging
from typing import List

from fastapi import FastAPI

from query_scanner import QueryScanner
from youtube_storage import YouTubeStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeSearcherAppException(Exception):
    pass

class YouTubeSearcherApp:
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

    @classmethod
    def reset_singleton(cls):
        cls._instance = None

    def __init__(self):

        if not hasattr(self, 'initialized'):
            self.initialized = False
        elif self.initialized:  # to ensure that heavy initialization is only done once
            return

        # ...heavy initialization...
        self.fast_api_app = FastAPI()
        self.setup_routes()
        logger.info("the YouTubeSearcherApp instance has FastAPI app with public routes loaded")

        self.storage = YouTubeStorage.get_singleton()
        logger.info("the YouTubeSearcherApp instance initialized with the YouTubeStorage instance")

        self.scanner = QueryScanner.get_singleton()
        logger.info("the YouTubeSearcherApp instance initialized with the QueryScanner instance")

        self.initialized = True  # Flag to show heavy initialization has been done

    def get_fast_api_app(self):
        """ Return the FastAPI app instance """
        return self.fast_api_app

    def setup_routes(self):
        def list_querys():
            """ scan all response items to create a list of all unique query values """
            return self.storage.find_all_querys()

        def list_responses(query: str):
            """ return a list of responses from requests with query """
            return self.storage.find_response_ids_by_query(query)

        def list_snippets(response_id: str):
            """ return the list of snipped associated with the given response_id """
            return self.storage.find_snippets_by_response_id(response_id)

        self.fast_api_app.get("/queries", response_model=List[dict])(list_querys)
        self.fast_api_app.get("/responses/{query}", response_model=List[dict])(list_responses)
        self.fast_api_app.get("/snippets/{response_id}", response_model=List[dict])(list_snippets)

if __name__ == "__main__":
    logger.info("Welcome to YouTubeSearcherApp")
    app_instance = YouTubeSearcherApp.get_singleton()
    app = app_instance.get_fast_api_app()
