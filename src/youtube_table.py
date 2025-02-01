from typing import Dict
import boto3
import requests
from botocore.exceptions import ClientError

class YouTubeTable:
    def __init__(self, table_name=None, config_url=None, endpoint_url=None):
        self.dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        if config_url:
            response = requests.get(config_url, timeout=10)
            config = response.json()
            table_name = config['TableName']
        self.table = self.dynamodb.Table(table_name)
        self.rows_to_insert = []

    def insert_row(self, row: Dict[str, str]) -> None:
        self.rows_to_insert.append(row)

    def insert_rows(self) -> None:
        try:
            with self.table.batch_writer() as batch:
                for row in self.rows_to_insert:
                    batch.put_item(Item=row)
            self.rows_to_insert.clear()
        except (ClientError) as error:
            print(f"An error occurred: {error}")
