import pytest
from moto import mock_aws
from boto3 import resource
from youtube_storage import YouTubeStorage

@pytest.fixture(scope="function")
def dynamodb():
    with mock_aws():
        dynamodb_resource = resource('dynamodb', region_name='us-east-1')

        # Create the 'Responses' table
        responses_table = dynamodb_resource.create_table(
            TableName='Responses',
            KeySchema=[
                {
                    'AttributeName': 'responseId',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'responseId',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        responses_table.meta.client.get_waiter('table_exists').wait(TableName='Responses')

        # Create the 'Snippets' table
        snippets_table = dynamodb_resource.create_table(
            TableName='Snippets',
            KeySchema=[
                {
                    'AttributeName': 'responseId',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'videoId',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'responseId',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'videoId',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        snippets_table.meta.client.get_waiter('table_exists').wait(TableName='Snippets')

        yield dynamodb_resource

@pytest.fixture(scope="function")
def youtube_storage(dynamodb):
    try:
        yield YouTubeStorage(dynamodb_resource=dynamodb)
    except dynamodb.meta.client.exceptions.ResourceInUseException as error:
        pytest.fail(f"Failed to set up mock DynamoDb tables: {error}")