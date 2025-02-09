import boto3

def count_tables():
    dynamodb = boto3.client('dynamodb', endpoint_url='http://localhost:4566', region_name='us-west-2')
    response = dynamodb.list_tables()
    table_count = len(response['TableNames'])
    print(f"Number of tables: {table_count}")

if __name__ == "__main__":
    count_tables()
