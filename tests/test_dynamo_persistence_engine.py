import os
import pytest
from moto import mock_dynamodb2
from boto3.exceptions import ClientError

import boto3


from ..src.dynamo_persistence_engine import DynamoPersistenceEngine

@pytest.fixture
def dynamo_mock():
    with mock_dynamodb2():
        yield

@pytest.fixture
def dynamo_persistence_engine(dynamo_mock):
    table_name = 'TestTable'
    endpoint_url = 'http://localhost:4566'
    engine = DynamoPersistenceEngine(table_name, endpoint_url)

    # Create the table
    engine.dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'etag', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'etag', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    return engine

def test_insert_resource_row(dynamo_persistence_engine):
    resource_row = {
        'etag': '12345',
        'kind': 'youtube#video',
        'nextPageToken': 'token',
        'regionCode': 'US',
        'pageInfo.totalResults': 100,
        'pageInfo.resultsPerPage': 10
    }
    dynamo_persistence_engine.insert_resource_row(resource_row)
    response = dynamo_persistence_engine.resource_table.get_item(Key={'etag': '12345'})
    assert 'Item' in response
    assert response['Item']['etag'] == '12345'

def test_insert_rows(dynamo_persistence_engine):
    rows = [
        {
            'etag': '12345',
            'kind': 'youtube#video',
            'nextPageToken': 'token1',
            'regionCode': 'US',
            'pageInfo.totalResults': 100,
            'pageInfo.resultsPerPage': 10
        },
        {
            'etag': '67890',
            'kind': 'youtube#video',
            'nextPageToken': 'token2',
            'regionCode': 'CA',
            'pageInfo.totalResults': 200,
            'pageInfo.resultsPerPage': 20
        }
    ]
    for row in rows:
        dynamo_persistence_engine.insert_row(row)
    dynamo_persistence_engine.insert_rows()

    response1 = dynamo_persistence_engine.resource_table.get_item(Key={'etag': '12345'})
    response2 = dynamo_persistence_engine.resource_table.get_item(Key={'etag': '67890'})

    assert 'Item' in response1
    assert response1['Item']['etag'] == '12345'
    assert 'Item' in response2
    assert response2['Item']['etag'] == '67890'


def test_dynamo_table(dynamo_persistence_engine):
    try:
        dd = dynamo_persistence_engine
        my_table = dd.create_dunamo_table(
            tableName='MyTable',
            partitionKey={'name': 'id', 'type': 'S'},  # 'S' for String, 'N' for Number
            sortKey={'name': 'timestamp', 'type': 'N'},  # Optional
            allKeys=[
                {'name': 'username', 'type': 'S'},
                {'name': 'status', 'type': 'S'}
            ])

        my_data = [
            {
                "id": "id1",
                "timeStamp": "2025-02-01T04:25:05 UTC",
                "userName": "Bobby",
                "status": "Alive"
            },
            {
                "id": "id2",
                "timeStamp": "2025-02-02T04:25:05 UTC",
                "userName": "Absher",
                "status": "Thriving"
            },
            {
                "id": "id3",
                "timeStamp": "2025-02-02T04:25:05 UTC",
                "userName": "Xinju",
                "status": "Fishing"
            }
        ]
        dd.insert_rows(my_table, my_data)

        db_data = my_table.selectAll()
        if db_data is None:
            raise ClientError({"Error": {"Code": "TableCreateFailed", "Message": "table create failed"}}, "CreateTable")
        my_keys = set(my_data[0].keys())
        db_keys = set(db_data[0].keys())
        if db_keys != my_keys:
            raise ClientError({"Error": {"Code": "KeysMismatch", "Message": "keys don't match"}}, "KeysMismatch")
        if len(db_data) != len(my_data):
            raise ClientError({"Error": {"Code": "LengthMismatch", "Message": "lengths don't match"}}, "LengthMismatch")
        for key in my_keys:
            db_value = db_data[key]
            my_value = my_data[key]
            if db_value != my_value:
                raise ClientError({"Error": {"Code": "ValueMismatch", "Message": f"key:{key} db_value:{db_value} != my_value:{my_value}"}}, "ValueMismatch")

        my_table.deleteRows()
        my_table.delete()
    except ClientError as error:
        print(f"ClientError: {error}")

