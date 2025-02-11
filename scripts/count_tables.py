import boto3
import json
from json import JSONDecodeError
from dynamodb_utils.json_utils import DynamoDbJsonUtils

dynamodb = boto3.client('dynamodb', endpoint_url='http://localhost:4566', region_name='us-west-2')

def get_table_config(table_name):
    table_description = dynamodb.describe_table(TableName=table_name)
    tableNameText = f"\"{table_name}\""
    keySchema = table_description['Table']['KeySchema']
    keySchemaText = DynamoDbJsonUtils.json_dumps(keySchema,indent=4)
    attrDefs = table_description['Table']['AttributeDefinitions']
    attrDefsText = DynamoDbJsonUtils.json_dumps(attrDefs,indent=4)
    provThruPut = table_description['Table']['ProvisionedThroughput']
    provThruPutText = DynamoDbJsonUtils.json_dumps(provThruPut,indent=4)

    configs = []
    configs.append(f"   \"TableName\": {tableNameText}")
    configs.append(f"   \"KeySchema\": {keySchemaText}")
    configs.append(f"   \"AttributeDefinitions\": {attrDefsText}")
    configs.append(f"   \"ProvisionedThroughput\": {provThruPutText}")
    config_text = "{\n" + ",\n".join(configs) + "\n}"

    table_config = json.loads(config_text)
    return table_config

def count_tables():
    response = dynamodb.list_tables()
    table_count = len(response['TableNames'])
    print(f"Number of tables: {table_count}")

    for table_name in response['TableNames']:
        table_description = dynamodb.describe_table(TableName=table_name)
        item_count = table_description['Table']['ItemCount']
        print(f"table: {table_name}")
        print(f"item_count: {item_count}")

        table_config = get_table_config(table_name)
        print(f"table_config:\n{json.dumps(table_config, indent=4)}")

if __name__ == "__main__":
    count_tables()
