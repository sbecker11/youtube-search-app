from dynamodb_utils.dbtypes import *

class DynamoDbTableUtils:

    @staticmethod
    def get_table_config(table_name):
        table_description = dynamodb.describe_table(TableName=table_name)
        tableNameText = f"\"{table_name}\""

        # extracted = {}
        # parent_property = "Table"
        # extracted_propertiess = ["TableName","KeySchema","AttributeDefinitions","ProvisionedThroughput"]

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
