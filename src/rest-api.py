from fastapi import FastAPI
import boto3
from typing import List

app = FastAPI()

dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4566')
responses_table = dynamodb.Table('Responses')
snippets_table = dynamodb.Table('Snippets')

@app.get("/subjects", response_model=List[str])
def list_subjects():
    response = responses_table.scan(ProjectionExpression="subject")
    subjects = {item['subject'] for item in response['Items']}
    return list(subjects)

@app.get("/responses/{subject}", response_model=List[dict])
def list_responses(subject: str):
    response = responses_table.query(
        IndexName='subject-index',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('subject').eq(subject)
    )
    return response['Items']

@app.get("/snippets/{response_id}", response_model=List[dict])
def list_snippets(response_id: str):
    response = snippets_table.query(
        IndexName='responseId-index',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('responseId').eq(response_id)
    )
    return response['Items']