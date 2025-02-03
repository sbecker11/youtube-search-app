from typing import List
from fastapi import FastAPI
from youtube_storage import YouTubeStorage

class YouTubeStorageApi:
    def __init__(self):
        self.app = FastAPI()
        self.storage = YouTubeStorage()
        self.setup_routes()

    def get_app(self):
        """ Return the FastAPI app instance """
        return self.app

    def setup_routes(self):
        def list_subjects():
            """ scan all response items to create a list of all unique subject values """
            return self.storage.find_all_subjects()

        def list_responses(subject: str):
            """ return a list of responses from requests with subject """
            return self.storage.find_response_ids_by_subject(subject)

        def list_snippets(response_id: str):
            """ return the list of snipped associated with the given response_id """
            return self.storage.find_snippets_by_response_id(response_id)

        self.app.get("/subjects", response_model=List[dict])(list_subjects)
        self.app.get("/responses/{subject}", response_model=List[dict])(list_responses)
        self.app.get("/snippets/{response_id}", response_model=List[dict])(list_snippets)

youtube_storage_api = YouTubeStorageApi()
app = youtube_storage_api.app
