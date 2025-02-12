import json
import logging
from typing import List, Dict
from time import sleep

import requests
import uvicorn
from fastapi import FastAPI
from openapi_spec_validator import validate_spec

from query_scanner import QueryScanner
from youtube_storage import YouTubeStorage
from dynamodb_utils.json_utils import DynamoDbJsonUtils
# global app run mode
APP_RUN_MODES = DynamoDbJsonUtils.load_json_file("APP_RUN_MODES.json")

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
        logger.info("the YouTubeSearcherApp instance initialized with FastAPI app with public routes loaded")

        self.storage = YouTubeStorage.get_singleton()
        logger.info("the YouTubeSearcherApp instance initialized with the YouTubeStorage instance")

        if APP_RUN_MODES['USE_SCANNER'] != 'no' and APP_RUN_MODES['SEND_YOUTUBE_QUERIES'] != "no":
            self.scanner = QueryScanner.get_singleton()
            logger.info("the YouTubeSearcherApp instance initialized with the QueryScanner instance")
        else:
            logger.info("the YouTubeSearcherApp instance DID NOT initialize with the QueryScanner instance")

        self.initialized = True  # Flag to show heavy initialization has been done

    def get_fast_api_app(self):
        """ Return the FastAPI app instance """
        return self.fast_api_app

    def run_fast_api_app(self, host="localhost", port=8000):
        """ start the FastAPI service listening at http://localhost:8000 """
        uvicorn.run(self.fast_api_app, host=host, port=port)

    def setup_routes(self):
        @self.fast_api_app.get("/")
        def read_root():
            return {"message": "Welcome to YouTubeSearcherApp"}

        @self.fast_api_app.get("/favicon.ico")
        def favicon():
            return {"message": "Favicon not found"}

        def list_querys():
            """ scan all response items to create a list of all unique query values """
            queries = self.storage.find_all_distinct_querys()
            # Return a single dictionary with a key mapping to the list of queries
            return {"queries": queries}

        def list_responses(query: str):
            """ return a list of responses from requests with query """
            return self.storage.find_response_ids_by_query(query)

        def list_snippets(response_id: str):
            """ return the list of snipped associated with the given response_id """
            return self.storage.find_snippets_by_response_id(response_id)

        self.fast_api_app.get("/queries", response_model=Dict[str, List[str]])(list_querys)
        self.fast_api_app.get("/responses/{query}", response_model=List[dict])(list_responses)
        self.fast_api_app.get("/snippets/{response_id}", response_model=List[dict])(list_snippets)

    def verify_navigation_requests(self) -> bool:
        """ Return True if all navigation requires used by FastAPI routes return values
            within the given MAX_FAILED_ATTEMPTS with SLEEP_SECS pause between attempts,
            Otherwise return false if still no results are found after MAX_FAILED_ATTEMPTS.
        """
        num_attempts = 0
        MAX_FAILED_ATTEMPTS = 5
        SLEEP_SECS = 5.0
        while num_attempts <= MAX_FAILED_ATTEMPTS:
            try:
                queries = self.storage.find_all_distinct_querys()
                assert len(queries) > 0
                # test_query = queries[0]
                # response_ids = self.storage.find_response_ids_by_query(test_query)
                # assert len(response_ids) >  0
                # test_response_id = response_ids[0]
                # snippets = self.storage.find_snippets_by_response_id(test_response_id)
                # assert len(snippets) > 0
                logger.info("Storage functions verified successfully")
                return True
            except AssertionError as error:
                logger.warning("Assertion error while verifying storage functions: %s", {error})
            num_attempts += 1
            sleep(SLEEP_SECS)
        logger.error("returning False after %d failed attempts", MAX_FAILED_ATTEMPTS)
        return False



    @staticmethod
    def main():
        logger.info("Welcome to YouTubeSearcherApp")
        searcher = YouTubeSearcherApp.get_singleton()

        if APP_RUN_MODES['USE_SCANNER'] == 'once':
            def on_scan_complete():
                searcher.verify_navigation_requests()
                searcher.run_fast_api_app(host="localhost", port=8000)
                logger.info("open FastAPI at http://localhost:8000")

            searcher.scanner.run_once(on_scan_complete)

        else:
            searcher.verify_navigation_requests()
            searcher.run_fast_api_app(host="localhost", port=8000)
            logger.info("open FastAPI at http://localhost:8000")


if __name__ == "__main__":
    YouTubeSearcherApp.main()
