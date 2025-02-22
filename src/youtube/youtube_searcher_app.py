import json
import logging
from typing import List
from time import sleep

import requests
import uvicorn
from fastapi import FastAPI
from openapi_spec_validator import validate_spec

from youtube.query_scanner import QueryScanner
from youtube.youtube_storage import YouTubeStorage
from dynamodb_utils.json_utils import DynamoDbJsonUtils
from dynamodb_utils.dbtypes import *

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


        # List all queries
        @self.fast_api_app.get("/queries", response_model=List[str])
        def list_queries():
            return self.list_queries()

        # List all response_ids for a given query
        @self.fast_api_app.get("/responses/{query}", response_model=List[str])
        def list_response_ids_with_query(query: str):
            return self.list_response_ids_with_query(query)
    

        @self.fast_api_app.get("/snippets/{responseId}", response_model=List[DbItem])
        def list_snippets_with_response_id(responseId: str):
            return self.list_snippets_with_response_id(responseId)

    def list_queries(self) -> List[str]:
        """ scan all response items to create a list of all unique query values """
        responses = self.storage.scan_table_items("Responses")

        # debug response attributes
        if len(responses) == 0:
            raise YouTubeSearcherAppException("No responses found in the database")
        # print(f"responses[0]: {DynamoDbJsonUtils.json_dumps(responses[0], indent=4)}")
        query_attribute = 'queryDetails.q'
        query_values = list(set([response[query_attribute] for response in responses]))
        if len(query_values) == 0:
            logger.warning(f"Zero query_values for {len(responses)} responses")
        return query_values

    def list_response_ids_with_query(self, query_value: str) -> List[str]:
        """ return a list of response_ids from requests with the given query_value """
        responses = self.storage.scan_table_items("Responses")
        query_attribute = 'queryDetails.q'
        distinct_response_ids = list(set([response['response_id'] for response in responses if response[query_attribute] == query_value]))
        if len(distinct_response_ids) == 0:
            logger.warning("Zero response_ids for query_value: %s", query_value)
        return distinct_response_ids

    def list_snippets_with_response_id(self, response_id: str) -> List[DbItem]:
        """ return the list of snipped associated with the given response_id """
        if not self.storage.is_valid_response_id(response_id):
            raise YouTubeSearcherAppException("response_id cannot be empty string")
        snippets = self.storage.scan_table_items("Snippets")
        snippets_with_response_id = [snippet for snippet in snippets if snippet["response_id"] == response_id]
        if len(snippets_with_response_id) == 0:
            logger.warning(f"Zero snippets found for response_id: {response_id}")
        return snippets_with_response_id

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
                queries = self.list_queries()
                assert len(queries) > 0
                test_query = queries[0]
                response_ids = self.list_response_ids_with_query(test_query)
                print(f"@@@@ response_ids: {response_ids}")
                assert len(response_ids) >  0
                test_response_id = response_ids[0]
                snippets = self.list_snippets_with_response_id(test_response_id)
                assert len(snippets) > 0
                logger.info("List functions verified successfully")
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
            def doit():
                searcher.verify_navigation_requests()
                searcher.run_fast_api_app(host="localhost", port=8000)
                logger.info("open FastAPI at http:/localhost:8000")

            searcher.scanner.run_once( doit )


if __name__ == "__main__":
    YouTubeSearcherApp.main()
