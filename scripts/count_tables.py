import boto3
import json
from dynamodb_utils.json_utils import DynamoDbJsonUtils
from youtube.youtube_table import YouTubeTable
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

DYNAMODB_URL = os.getenv("DYNAMODB_URL")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
dynamodb = boto3.client('dynamodb', endpoint_url=DYNAMODB_URL, region_name=AWS_DEFAULT_REGION)

def count_tables():
    response = dynamodb.list_tables()
    table_count = len(response['TableNames'])
    print(f"Number of tables: {table_count}")

    for table_name in response['TableNames']:
        table_description = dynamodb.describe_table(TableName=table_name)
        item_count = table_description['Table']['ItemCount']
        print(f"table: {table_name}")
        print(f"item_count: {item_count}")

        table_config = YouTubeTable.get_dbTable_config(table_name=table_name)
        print(f"table_config:\n{json.dumps(table_config, indent=4)}")

if __name__ == "__main__":
    count_tables()
