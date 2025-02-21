# Overview of the YouTube Search App project


```tree
.
├── Dockerfile
├── README.md
├── data
│   ├── query_response_head.json
│   ├── query_response_item.json
│   ├── query_scanner_config.json
│   ├── responses_table_config.json
│   └── snippets_table_config.json
├── data_processor
│   ├── Dockerfile
│   └── app.py
├── dist
│   └── youtube-search-api.egg-info
│       ├── PKG-INFO
│       ├── SOURCES.txt
│       ├── dependency_links.txt
│       └── top_level.txt
├── docker-compose-dynamodb-only.yml
├── docker-compose.yml
├── jest.config.js
├── localstack.pid
├── requirements.txt
├── responses-clipped.json
├── responses.scan
├── scripts
│   ├── count-tables
│   ├── count_tables.py
│   ├── generate-docs
│   ├── generate-docs-with-redoc
│   ├── run-app
│   ├── run-docker-compose.scpt
│   ├── run-dynamo
│   └── run-pytest
├── src
│   ├── Dockerfile
│   ├── __init__.py
│   ├── dynamodb_utils.py
│   ├── query_engine.py
│   ├── query_scanner.py
│   ├── youtube_searcher_app.py
│   ├── youtube_storage.py
│   └── youtube_table.py
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_conftest.py
    ├── test_query_engine.py
    ├── test_query_scanner.py
    ├── test_youtube_storage.py
    ├── test_youtube_storage_api.py
    └── test_youtube_table.py
```


This docker-compose project creates a local-dynamodb image that runs in a localstack image on local DockerDesktop. `Dockerfile` and `docker-compose.yaml` reside at project-root, and are used to deploy assets to DockerDesktop.

QueryEngine in `src/query_engine.py` sends a variety of RESTful search queries to the YouTubeMetadataAPI. Query `request` and `response` data access operations are handled by the YouTubeStorage object. Example query response data may be found in /data/query_response_head.json and query_response_item.json

Search query requests and responses are stored in the Responses dynamoDb tables by YouTubeStorage in `src/youtube_storage.py`. Each response record is given a unique primary key named `etag` and stored in the Dynamo `Responses` table. All snippets stored in a `Snippets` table and refer to foreign key `etag`. Dyanamo table definitions for these tables reside at `/data/responses_table_config.json` and `/data/snippets_table_config.json`

YouTubStoreageApi from `src/youtube_searcher_app.py` uses FastAPI to handle queries made by project users against YouTubeStorage. OpenAI documentation is created during `docker-compose up --build` and resides at `/docs`.

QueryScanner in `src/query_scanner.py` is a singleton object that uses `croniter` and `schedule` to run a batch of queries to the YouTubeAPI via QueryEngine. The set to queries and the cron schedule are stored at `/data/query_scanner_config.json`.

Credentials for YouTube and AWS are stored in a local `.env` file, which is never uploaded to the remote github repo.

The structure of the `.env` file is:
```text
YOUTUBE_API_KEY=*****
AWS_ACCESS_KEY_ID=*****
AWS_SECRET_ACCESS_KEY_ID=*****
AWS_DEFAULT_REGION=us-west-2
DYNAMODB_URL=http://localstack:4566
RESPONSES_CONFIG_PATH=./data/responses_table_config.json
SNIPPETS_CONFIG_PATH=./data/snippets_table_config.json
QUERY_SCANNER_CONFIG_PATH=./data/query_scanner_config.json
MAX_QUERIES_PER_SCAN=100
```

Docker configuration files are found at project root. Python source modules are found at project root under the `src` directory. Pytest modules are found in `/tests` OpenAPI documentation files are found in `/docs`.

### Useful aws-cli commands for querying the dynamodb tables:
count the number of tables:
```bash
aws dynamodb list-tables --endpoint-url http://localhost:4566 --region us-west-2 | jq '.TableNames | length'
```
list all tables:
>```bash
aws dynamodb list-tables --endpoint-url http://localhost:4566 --region us-west-2
```
describe the Responses table
```bash
aws dynamodb describe-table --table-name Responses \
    --endpoint-url http://localhost:4566 --region us-west-2
```
describe the Snippets table
```bash
ws dynamodb describe-table --table-name Snippets \
    --endpoint-url http://localhost:4566 --region us-west-2
```

### pipe the aws query results to jq to extract the queryDetails.query
from each item:
```bash
aws dynamodb scan --table-name Responses \
--endpoint-url http://localhost:4566 \
--region us-west-2 | \
jq -r '.Items[] | .queryDetails.M.q.S'
```
### An fairly involved query:
```bash
 aws dynamodb query \
    --table-name Responses \
    --key-condition-expression "#etag = :etagval" \
    --expression-attribute-values '{":etagval":{"S":"SpH9JnQTah47E6gjAFSuzA76c8M"}}' \
    --expression-attribute-names '{"#etag":"response.etag", "#queryDetails":"queryDetails", "#receivedAt":"responseReceivedAt"}' \
    --endpoint-url http://localhost:4566 \
    --region us-west-2 \
    --projection-expression "#etag, #queryDetails, #receivedAt" \
    --select SPECIFIC_ATTRIBUTES
```
with a detailed Explanation:

1. **`aws dynamodb query`** - This command initiates a query operation on DynamoDB.

2. **`--table-name Responses`** - Specifies the name of the table you're querying, which in this case is `"Responses"`.

3. **`--key-condition-expression "#etag = :etagval"`**:
   - `#etag` is a placeholder for an attribute name.
   - `=` is the condition operator for equality.
   - `:etagval` is a placeholder for the value you're comparing against.
   - This condition filters items where the `response.etag` attribute equals the specific value provided.

4. **`--expression-attribute-values '{":etagval":{"S":"SpH9JnQTah47E6gjAFSuzA76c8M"}}'`** - Defines the actual value for `:etagval`. Here, `"S"` indicates it's a String type, and the value is the `etag` you're searching for.

5. **`--expression-attribute-names '{"#etag":"response.etag", "#queryDetails":"queryDetails", "#receivedAt":"responseReceivedAt"}'`** -
   - Maps placeholders (`#etag`, `#queryDetails`, `#receivedAt`) to the actual attribute names in your table.
   - This is necessary because `response` is a reserved word in DynamoDB expressions, so we need to escape it.

6. **`--endpoint-url http://localhost:4566`** - Specifies that this query should be sent to a local DynamoDB instance running on port `4566`, which is commonly used for DynamoDB Local or DynamoDB in Docker for development purposes.

7. **`--region us-west-2`** - Indicates the AWS region to use. Even for local instances, specifying a region can be necessary for some AWS CLI operations.

8. **`--projection-expression "#etag, #queryDetails, #receivedAt"`** -
   - This specifies which attributes to return in the result set.
   - Here, we're asking for `response.etag`, `queryDetails`, and `responseReceivedAt`.
   - Using placeholders ensures we avoid issues with reserved keywords.

9. **`--select SPECIFIC_ATTRIBUTES`** -
   - Tells DynamoDB to return only the attributes specified in the projection expression, rather than the entire item.
   - This can significantly reduce the amount of data transferred, improving performance.

aws dynamodb put-item --table-name MyTable \
    --item '{"id": {"S": "123"}, "name": {"S": "Test Item"}}' \
    --endpoint-url http://localhost:4566 --region us-west-2

aws dynamodb delete-item --table-name MyTable \
    --key '{"id": {"S": "123"}}' \
    --endpoint-url http://localhost:4566 --region us-west-2

<!-- aws configure set aws_access_key_id fakeKey --profile local
aws configure set aws_secret_access_key fakeSecret --profile local
aws configure set region us-west-2 --profile local -->

# sort
aws dynamodb query \
    --table-name MyTable \
    --key-condition-expression "partitionKey = :pk" \
    --expression-attribute-values '{":pk": {"S": "someValue"}}' \
    --scan-index-forward false \
    --limit 10 \
    --endpoint-url http://localhost:4566 --region us-west-2

--scan-index-forward false → Retrieves the latest items first.

Replace partitionKey with your actual primary key.

if no paritioni key:
aws dynamodb scan \
    --table-name MyTable \
    --endpoint-url http://localhost:4566 --region us-west-2 \
    --query 'Items | sort_by(@, &timestamp) | reverse(@)[:10]'

The reverse(@)[:10] gets the last 10 items.

boto3 queries

count number of tables:
???

# Query with sorting (assuming timestamp exists)
response = table.query(
    KeyConditionExpression="partitionKey = :pk",
    ExpressionAttributeValues={":pk": "someValue"},
    ScanIndexForward=False,  # Fetch latest records first
    Limit=10
)
# Print results
for item in response['Items']:
    print(item)

SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Responses'

SELECT DISTINCT AttributeName FROM TableName

SELECT AttributeName FROM TableName GROUP BY AttributeName



import boto3
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('YourTableName')

unique_values = defaultdict(set)
response = table.scan()
for item in response['Items']:
    if 'AttributeName' in item:
        unique_values['AttributeName'].add(item['AttributeName'])

print(unique_values['AttributeName'])

    raise QueryEngineException(error)


```





important links:
http://localhost:8000 link to the YouTubeSearcherApp

Object Relationships

    User --------------- uses YouTubeSearcherApp URL
    User --------------- queries data --------------------- YouTubeSearcherApp
app YouTubeSearcherApp -- queries data in ------------------ YouTubeStorage
    YouTubeStorage ----- uses AWS access keys in .env
    QueryEngine -------- uses YOUTUBE_API key in .env
    QueryEngine -------- sends request to ----------------- YouTube-Metadata-API (external)
    QueryEngine -------- saves request+response to -------- YouTubeStorage
app QueryScanner ------- uses /data/query_scanner_config.json
app QueryScanner ------- calls QueryEngine

Project Structure:
```tree
.
├── README.md
├── data
│   ├── query_response_head.json
│   ├── query_response_item.json
│   ├── query_scanner_config.json
│   ├── responses_table_config.json
│   └── snippets_table_config.json
├── data_processor
│   ├── Dockerfile
│   └── app.py
├── docker-compose.yml
├── jest.config.js
├── localstack.pid
├── requirements.txt
├── scripts
│   └── run-pytest
├── src
│   ├── Dockerfile
│   ├── __init__.py
│   ├── query_engine.py
│   ├── query_scanner.py
│   ├── youtube_storage.py
│   ├── youtube_searcher_app.py
│   └── youtube_table.py
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_conftest.py
    ├── test_query_engine.py
    ├── test_query_scanner.py
    ├── test_youtube_storage.py
    ├── test_youtube_searcher_app.py
    └── test_youtube_table.py
```

# YouTube Search API

## Verifying Docker Desktop is Running

To verify that Docker Desktop is running, you can follow these steps:

1. **Check Docker Desktop Application**: Open the Docker Desktop application on your computer. If it is running, you should see the Docker icon in your system tray (Windows) or menu bar (Mac).

2. **Use Command Line**: Open a terminal and run the following command to check the status of Docker:

```sh
docker info
```

If Docker Desktop is running, this command will display detailed information about your Docker installation, including the server version, storage driver, and other configuration details.

3. **Check Docker Services**: You can also list the running Docker containers to ensure that your services are up and running:

```sh
docker ps
```

This command will display a list of all running containers, including their container IDs, names, and status.

## Running LocalStack with DynamoDb

To start the LocalStack service with DynamoDb, use the following command:

```sh
docker-compose -f docker-compose-dynamodb-only.yml up
```

To stop the services, use:

```sh
docker-compose -f docker-compose-dynamodb-only.yml down
```

YouTube Open AI Specification

https://developers.google.com/youtube/v3/docs
 https://www.googleapis.com/youtube/v3

Search Result Spec
JSON structure shows the format of a search result
https://developers.google.com/youtube/v3/docs/search

YouTubeAPIWrapper
git@github.com:pdrm83/youtube_api_wrapper.git

## Search Videos
```python
from youtube_easy_api.easy_wrapper import *

easy_wrapper = YoutubeEasyWrapper()
easy_wrapper.initialize(api_key=API_KEY)
results = easy_wrapper.search_videos(search_keyword='python', order='relevance')
order_id = 1
video_id = results[order_id]['video_id']

print(video_id)
'_uQrJ0TkZlc'
```

### Extract Metadata
```python
from youtube_easy_api.easy_wrapper import *

easy_wrapper = YoutubeEasyWrapper()
easy_wrapper.initialize(api_key=API_KEY)
metadata = easy_wrapper.get_metadata(video_id='rdjnkb4ONWk')

print(metadata['title'])
'The Pink Panther Show Episode 59 - Slink Pink'

print(metadata['statistics']['likeCount'])
285373
```



### Docker build command
```bash
cd /Users/sbecker11/workspace-youtubeyoutube-search-app
docker compose -f docker-compose-dynamodb-only-no-volumes.yml up
```

### Run scanner command
```
APP_CONTAINER_ID=$(docker ps | grep "youtube-search-app-app" | awk '{print $1}')
echo "$APP_CONTAINER_ID"
docker exec -it $APP_CONTAINER_ID python run_scanner.py
```

### API Endpoints
`http://localhost:5000/headers` Endpoint to query the query headers stored in dynamodb
`http://localhost:5000/items` Endpoint to query the items stored in dynamodb


### API Documentation
`http://localhost:5000/docs` Swagger UI to access the interactive Swagger UI documentation
`http://localhost:5000/redoc` ReDoc to access the clean and readable ReDoc documentation

Example YouTubeMetadata API requests
list videos relating to "coding tutorials"
https://www.googleapis.com/youtube/v3/search?part=snippet&q=coding+tutorials&key=YOUR_API_KEY



finally got dynamodb saving data to local disk:

steps 1. create a docker-config.yml that only lists localstack with dynamodb service

```yml
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"  # LocalStack Edge Proxy
      - "8080:8080"  # LocalStack Dashboard
    environment:
      - SERVICES=dynamodb
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
    volumes:
      - /Users/sbecker11/xyz/tmp/localstack:/tmp/localstack
      - /Users/sbecker11/xyz/tmp/.cache:/.cache
      - /var/run/docker.sock:/var/run/docker.sock
    user: "502:20"


# docker compose up localstack
# docker compose logs localstack
```

2. on local machine create
/Users/sbecker11/xyz/tmp/localstack
/Users/sbecker11/xyz/tmp/.cache:

chown -R 502:20 /Users/sbecker11/xyz/tmp
chmod -R 770    /Users/sbecker11/xyz/tmp

in docker desktop > settings > resources > file sharing
enter these folders manually (cut/paste)
/Users/sbecker11/xyz/tmp/localstack
/Users/sbecker11/xyz/tmp/.cache:

hit the apply and restart button

wait a few seconds then shutdown docker desktop
then start it up again and verify that the two
file sharing directories are still present in docker desktop

then go into the directory that has the docker-compose.yml file
and in a dedicated terminal run 
```bash
docker compose up localstack
```
or add -d to run it in detached mode

verify that dynamodb is responsive by running

```bash
aws --endpoint-url=http://localhost:4566 dynamodb list-tables 
```
and it lists zero tables

verify that localstack is listening on port 8080
```bash
open http://localhost:8080
```
see webpage message "It works!"

now let's create a table:
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name TestTable \
    --attribute-definitions AttributeName=Id,AttributeType=S \
    --key-schema AttributeName=Id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```
and more aws commands
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb put-item \
    --table-name TestTable \
    --item '{"Id": {"S": "2"}, "Name": {"S": "Another Item"}, "Description": {"S": "This is a test"}}'
```
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb scan \
    --table-name TestTable
```
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb update-item \
    --table-name TestTable \
    --key '{"Id": {"S": "1"}}' \
    --update-expression "SET #n = :newname" \
    --expression-attribute-names '{"#n":"Name"}' \
    --expression-attribute-values '{":newname":{"S":"Updated Name"}}'
```
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb scan \
    --table-name TestTable
```
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb delete-item \
    --table-name TestTable \
    --key '{"Id": {"S": "2"}}'
```
```bash
> aws --endpoint-url=http://localhost:4566 dynamodb scan \
    --table-name TestTable
```
```bash
aws --endpoint-url=http://localhost:4566 dynamodb delete-table \
    --table-name TestTable
```

verify data is being saved by checking 

```bash
> ll ~/xyz/tmp/localstack/state/dynamodb/
total 64
drwxr-xr-x  4 sbecker11  staff    128 Feb 16 23:33 ./
drwxr-xr-x  3 sbecker11  staff     96 Feb 16 23:27 ../
-rw-r--r--  1 sbecker11  staff  13312 Feb 16 23:27 000000000000_us-east-1.db
-rw-r--r--  1 sbecker11  staff  16384 Feb 16 23:33 000000000000uswest2_us-west-2.db
```

also see that the container is up and running using
```bash
> docker ps -a
CONTAINER ID   IMAGE                          COMMAND                  CREATED          STATUS                    PORTS                                                                     NAMES
7afc6c907786   localstack/localstack:latest   "docker-entrypoint.sh"   48 minutes ago   Up 44 minutes (healthy)   4510-4559/tcp, 0.0.0.0:4566->4566/tcp, 5678/tcp, 0.0.0.0:8080->8080/tcp   youtube-search-app-localstack-1
```

Now turn off docker desktop 

and then start it up again

find the container for youtube-search-app is still there
click to start it.
and run aws queries against it:

```bash
> aws --endpoint-url=http://localhost:4566 dynamodb list-tables
```
and the table is gone!
