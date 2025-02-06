import pytest
import boto3
from moto import mock_aws
from youtube_table import YouTubeTable

@pytest.fixture
def dynamodb():
    with mock_aws():
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
    config = {
        "TableName": "YouTubeTable",
        "KeySchema": [
            {
                "AttributeName": "id",
                "KeyType": "HASH"
            }
        ],
        "AttributeDefinitions": [
            {
                "AttributeName": "id",
                "AttributeType": "S"
            }
        ],
        "ProvisionedThroughput": {
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5
        }
    }
    return YouTubeTable(config)

def test_add_item(youtube_table):
    item = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_item(item)
    assert youtube_table.get_item({'id': '123'}) == item

def test_get_item(youtube_table):
    item = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_item(item)
    result = youtube_table.get_item({'id': '123'})
    assert result == item

def test_delete_item(youtube_table):
    item = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_item(item)
    youtube_table.delete_item({'id': '123'})
    assert youtube_table.get_item({'id': '123'}) is None

def test_scan_table(youtube_table):
    item1 = {'id': '123', 'title': 'Test Video 1'}
    item2 = {'id': '456', 'title': 'Test Video 2'}
    youtube_table.add_item(item1)
    youtube_table.add_item(item2)
    result = youtube_table.scan_table()
    assert item1 in result
    assert item2 in result

def test_update_item(youtube_table):
    item = {'id': '123', 'title': 'Test Video'}
    youtube_table.add_item(item)
    youtube_table.update_item(
        key={'id': '123'},
        update_expression="set title = :t",
        expression_attribute_values={':t': 'Updated Test Video'}
    )
    updated_item = youtube_table.get_item({'id': '123'})
    assert updated_item['title'] == 'Updated Test Video'

def test_query_table(youtube_table):
    item1 = {'id': '123', 'title': 'Test Video 1'}
    item2 = {'id': '456', 'title': 'Test Video 2'}
    youtube_table.add_item(item1)
    youtube_table.add_item(item2)
    result = youtube_table.query_table(
        key_condition_expression="id = :id",
        expression_attribute_values={':id': '123'}
    )
    assert item1 in result
    assert item2 not in result