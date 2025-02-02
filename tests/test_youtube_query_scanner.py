import sys
import os
import boto3
import pytest
from moto import mock_dynamodb

# Add project-root/src to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Add project-root/src to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture
def dynamodb():
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.create_table(
            TableName='QueryTable',
            KeySchema=[
                {'AttributeName': 'query', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'query', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        yield dynamodb

@pytest.fixture
def query_scanner(dynamodb_resource):
    return QueryScanner(dynamodb)

def test_scan_query(scanner):
    query = "test query"
    result = scanner.scan(query)
    assert result is not None
    assert 'results' in result

def test_scan_empty_query(scanner):
    query = ""
    result = scanner.scan(query)
    assert result is not None
    assert 'results' in result
    assert len(result['results']) == 0

def test_scan_special_characters(scanner):
    query = "!@#$%^&*()"
    result = scanner.scan(query)
    assert result is not None
    assert 'results' in result
