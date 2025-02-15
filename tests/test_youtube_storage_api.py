from moto import mock_aws2
import boto3
import pytest
from youtube_storage import YouTubeStorage

def test_add_query_response(youtube_storage):
    query_engine = {
        'subject': 'Python programming',
        'requestSubmittedAt': '2023-10-01T00:00:00Z',
        'part': 'snippet',
        'q': 'Python programming',
        'type': 'video',
        'maxResults': 25
    }
    youtube_response = {
        'etag': 'etag123',
        'kind': 'youtube#searchListResponse',
        'nextPageToken': 'CAUQAA',
        'regionCode': 'US',
        'pageInfo': {
            'totalResults': 1000000,
            'resultsPerPage': 25
        },
        'items': []
    }
    youtube_storage.add_query_response(query_engine, youtube_response)
    # Add assertions to verify the behavior
    table = youtube_storage.dynamodb.Table('Responses')
    response = table.get_item(Key={'response_id': youtube_response['etag']})
    assert 'Item' in response

    table = youtube_storage.dynamodb.Table('Snippets')
    response = table.query(KeyConditionExpression=Key('response_id').eq(youtube_response['etag']))
    assert response['Count'] == 0  # Since items are empty