import os
from typing import List
from fastapi import FastAPI
from youtube_storage import YouTubeStorage

class RestApi:
    def __init__(self):
        self.app = FastAPI()
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL', None)
        self.responses_table = self.dynamodb.Table('Responses')
        self.snippets_table = self.dynamodb.Table('Snippets')
        self.setup_routes()

    def setup_routes(self):
        def list_subjects():
            """ scan all response items to create a list of all unique subject values """
            subjects = set()
            response = self.responses_table.scan(ProjectionExpression="subject")
            subjects.update(item['subject'] for item in response['Items'])
            while 'LastEvaluatedKey' in response:
                response = self.responses_table.scan(
                    ProjectionExpression="subject",
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                subjects.update(item['subject'] for item in response['Items'])
            return list(subjects)

        def list_responses(subject: str):
            """ return a list of responses from requests with subject """
            response = self.responses_table.query(
                IndexName='subject-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('subject').eq(subject)
            )
            return response['Items']

        def list_snippets(response_id: str):
            """ return the list of snipped associated with the given response_id """
            response = self.snippets_table.query(
                IndexName='responseId-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('responseId').eq(response_id)
            )
            return response['Items']


        self.app.get("/subjects", response_model=List[dict])(list_subjects)
        self.app.get("/responses/{subject}", response_model=List[dict])(list_responses)
        self.app.get("/snippets/{response_id}", response_model=List[dict])(list_snippets)

rest_api = RestApi()
app = rest_api.app
