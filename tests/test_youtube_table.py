import pytest
import boto3
from moto import mock_dynamodb
from youtube_table import YouTubeTable

@pytest.fixture
def dynamodb():
    with mock_dynamodb():
        dynamodb_resource = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb_resource.create_table(
            TableName='YouTubeTable',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        yield dynamodb_resource

@pytest.fixture
def youtube_table(dynamodb):
    return YouTubeTable(dynamodb)

@mock_dynamodb
def test_add_video(youtube_table):
    video = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_video(video)
    assert youtube_table.get_video('123') == video

@mock_dynamodb
def test_get_video(youtube_table):
    video = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_video(video)
    result = youtube_table.get_video('123')
    assert result == video

@mock_dynamodb
def test_remove_video(youtube_table):
    video = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_video(video)
    youtube_table.remove_video('123')
    assert youtube_table.get_video('123') is None

@mock_dynamodb
def test_list_videos(youtube_table):
    video1 = {'id': '123', 'title': 'Test Video 1'}
    video2 = {'id': '456', 'title': 'Test Video 2'}
    youtube_table.add_video(video1)
    youtube_table.add_video(video2)
    result = youtube_table.list_videos()
    assert video1 in result
    assert video2 in result
