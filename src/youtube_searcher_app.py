import json
import logging
from typing import List

import requests
import uvicorn
from fastapi import FastAPI
from openapi_spec_validator import validate_spec

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

        self.run_scanner = False
        if self.run_scanner:
            self.scanner = QueryScanner.get_singleton()
            logger.info("the YouTubeSearcherApp instance initialized with the QueryScanner instance")

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


def save_openapi_docs(url, output_path='./docs/openapi.json'):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    spec = response.json()

    # Validate the OpenAPI spec
    validate_spec(spec)

    # Save the JSON to file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(spec, file, indent=2)

    print(f"OpenAPI spec saved to {output_path}")



if __name__ == "__main__":
    logger.info("Welcome to YouTubeSearcherApp")

    APP_INSTANCE = YouTubeSearcherApp.get_singleton()
    APP_INSTANCE.storage.find_all_querys()
    # APP_INSTANCE.run_fast_api_app(host="localhost", port=8000)
    # logger.info("open FastAPI at http:/localhost:8000")
