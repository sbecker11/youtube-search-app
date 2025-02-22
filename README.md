# Overview of the YouTube Search App project

## Project Structure
```  
youtube-search-app
├── APP_RUN_MODES.json
├── Dockerfile
├── README.md
├── data
│   ├── query_response_head.json
│   ├── query_response_item.json
│   ├── query_scanner_config.json
│   ├── responses_table_config.json
│   ├── snippets_table_config.json
│   └── table-storage.json
├── dist
│   └── youtube-search-api.egg-info
│       ├── PKG-INFO
│       ├── SOURCES.txt
│       ├── dependency_links.txt
│       └── top_level.txt
├── docker-compose.yml
├── docs
│   ├── index.html
│   ├── openapi.js
│   ├── openapi.json
│   └── redoc.html
├── jest.config.js
├── localstack.pid
├── latest_trends.txt
├── requirements.txt
├── scripts
│   ├── activate
│   ├── aws-test-table-create
│   ├── aws-test-table-delete
│   ├── aws-test-table-delete-item
│   ├── aws-test-table-put-item
│   ├── aws-test-table-run-tests
│   ├── aws-test-table-scan
│   ├── aws-test-table-update-item
│   ├── count-tables
│   ├── count-tables-items
│   ├── delete-tables
│   ├── dump-tables
│   ├── fetch-random-topics
│   ├── generate-open-api-docs
│   ├── load-tables
│   ├── run-app
│   ├── run-dynamo
│   ├── run-pytest
│   ├── run-scanner
│   └── scan-tables
├── special-installations
│   └── install-pyyaml-5.4.1
├── src
│   ├── dynamodb_utils
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── dbtypes.py
│   │   ├── dict_utils.py
│   │   ├── filter_utils.py
│   │   ├── item_utils.py
│   │   ├── json_utils.py
│   │   ├── latest_trends.py
│   │   ├── table_utils.py
│   │   └── validators.py
│   └── youtube
│       ├── __init__.py
│       ├── query_engine.py
│       ├── query_scanner.py
│       ├── youtube_api_docs.py
│       ├── youtube_searcher_app.py
│       ├── youtube_storage.py
│       └── youtube_table.py
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

# Screenshots

![01 - OpenApi HomePage](screenshots/01%20-%20OpenApi%20HomePage.png)
![02 - Get queries](screenshots/02%20-%20Get%20queries.png)
![03 - Get responses](screenshots/03%20-%20Get%20responses.png)
![04 - Get snippets](screenshots/04%20-%20Get%20snippets.png)
![05 - Get snippets bottom](screenshots/05%20-%20Get%20snippets%20bottom.png)


# Description

This docker-compose project creates a local-dynamodb image that runs in a localstack image on local DockerDesktop. `Dockerfile` and `docker-compose.yaml` reside at project-root, and are used to deploy assets to DockerDesktop.

The `QueryEngine` singleton in `src/youtube/query_engine.py` sends a variety of RESTful search queries to the YouTubeMetadataAPI. Query `request` and `response` data access operations are handled by the `YouTubeStorage` singleton at `src/youtube/youtube_storage.py`. Example query response data may be found in `/data/query_response_head.json` and `query_response_item.json`

Search query requests and responses are stored in the `Responses` table in dynamoDb by the `YouTubeStorage` singleton in `src/youtube_storage.py`. Each response record is given a unique primary key `reponse_id` and stored in the `Responses` table. All snippets with a given response are stored in the `Snippets` table and refer to foreign key `response_id`. Dyanamo table definitions for these tables reside at `/data/responses_table_config.json` and `/data/snippets_table_config.json`

The `QueryScanner` in `src/query_scanner.py` is a singleton object that uses `croniter` and `schedule` to run a batch of queries to the YouTubeAPI via the `QueryEngine`. The cron schedule is stored at `/data/query_scanner_config.json`.

The random set of queries that `QueryScanner` submits is obtained from `src/dynamodb_utils/latest_trends.py::fetch-latest-trends` which submits a request to `https://trends.google.com/trends/trendingsearches/daily/rss?geo=US` and stores the resulting list at `latest-trends.txt`

The `YouTubeSearcherApp` from `src/youtube/youtube_searcher_app.py` uses FastAPI to handle RESTful queries made by project users against `YouTubeStorage` to explore the DynamoDB tables. 

OpenAI documentation is created at `docs/` using `scripts\generate-open-api`. These pages may be used to make the following searches:

```bash
GET /queries      :  to Fetch a videos from YouTube metadata API for today trending topics  

GET /response_ids :  to Fetch all video responses for a given query  

GET /snippets     :  to Fetch all snippets for a given response_id  
```

# Credentials

Credentials for YouTube and AWS are stored in a local `.env` file, which is never uploaded to the remote github repo.

The structure of the `.env` file is:
```text
YOUTUBE_=*****
AWS__=*****
AWS__=*****
AWS_DEFAULT_REGION=us-west-2
DYNAMODB_URL=http://localstack:4566
RESPONSES_CONFIG_PATH=./data/responses_table_config.json
SNIPPETS_CONFIG_PATH=./data/snippets_table_config.json
QUERY_SCANNER_CONFIG_PATH=./data/query_scanner_config.json
MAX_QUERIES_PER_SCAN=3
```


# Configuration

Docker configuration files are found at project root. Python source modules are found at project root under the `src` directory. Pytest modules are found in `/tests` OpenAPI documentation files are found in `/docs`.


## docker-compose.yml
```
services:
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"  # LocalStack Edge Proxy
      - "8080:8080"  # LocalStack Dashboard
    environment:
      - SERVICES=dynamodb
      - DEBUG=1
      - PERSISTENCE=1
    volumes:
      - /Users/sbecker11/xyz/tmp/data:/var/lib/localstack
      - /Users/sbecker11/xyz/tmp/localstack:/tmp/localstack
      - /Users/sbecker11/xyz/tmp/.cache:/.cache
      - /var/run/docker.sock:/var/run/docker.sock

    user: "502:20"
    group_add:
      - dialout
      - staff
```

# DockerDesktop Settings > Resources > File Sharing
Set up file sharing for local side of shared volumes
```
/Users/sbecker11/xyz/tmp/data
/Users/sbecker11/xyz/tmp/localstack
/Users/sbecker11/xyz/tmp/.cache
/var/run/docker.sock
```

## Shared folders and files CHOWN and CHMOD  
Ensure that these shared folders and files have `chmod 770` and have the 
given userId 502 for myself, sbecker11, and the staff groupId 20 as 
defined in `docker-compose.yml`
```
sudo chown -R 502:20 /Users/sbecker11/xyz /var/run/docker.sock  
such chmod -R 770 /Users/sbecker11/xyz /var/run/docker.sock
```

## DynamoDB PERSISTENCE  
DynamoDb state is PERSISTED at `/var/lib/localstack` in docker
which maps to `/Users/sbecker11/xyz/tmp/data` on my host machine:
```
xyz/tmp/data/state
└── dynamodb
    ├── 000000000000_us-east-1.db
    └── 000000000000uswest2_us-west-2.db
```


# Useful Scripts and AWS Commands  

This script is sourced to setup PYTHONPATH and to verify running conditions of DockerDesktop, localstack, and dynamodb:
```bash
scripts/activate
```

This docker command is used to launch `localstack` with `dynamodb` on `DockerDesktop` in detached mode:  
```bash
docker compose up -d
```

These aws-cli commands are used to query the Dynamodb tables:
Count the number of tables:
```bash
aws dynamodb list-tables --endpoint-url http://localhost:4566 --region us-west-2 | jq '.TableNames | length'
```

List all tables:
```bash
aws dynamodb list-tables --endpoint-url http://localhost:4566 --region us-west-2
```

Describe the Responses table
```bash
aws dynamodb describe-table --table-name Responses \
    --endpoint-url http://localhost:4566 --region us-west-2
```

Describe the Snippets table
```bash
ws dynamodb describe-table --table-name Snippets \
    --endpoint-url http://localhost:4566 --region us-west-2
```

### Pipe the aws query results to jq to extract the queryDetails.query from each item:
```bash
aws dynamodb scan --table-name Responses \
--endpoint-url http://localhost:4566 \
--region us-west-2 | \
jq -r '.Items[] | .queryDetails.M.q.S'
```

### Fetch the responses entry for a given etag:
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

Put an item into "MyTable"
```
aws dynamodb put-item --table-name MyTable \
    --item '{"id": {"S": "123"}, "name": {"S": "Test Item"}}' \
    --endpoint-url http://localhost:4566 --region us-west-2
```
Delete the item
```
aws dynamodb delete-item --table-name MyTable \
    --key '{"id": {"S": "123"}}' \
    --endpoint-url http://localhost:4566 --region us-west-2
```

Sort the all items from a table
```
aws dynamodb query \
    --table-name MyTable \
    --key-condition-expression "partitionKey = :pk" \
    --expression-attribute-values '{":pk": {"S": "someValue"}}' \
    --scan-index-forward false \
    --limit 10 \
    --endpoint-url http://localhost:4566 --region us-west-2
```
Reverse sort
```
--scan-```index-forward false → Retrieves the latest items first.
```

Replace partitionKey with your actual primary key.

if no paritioni key:
```
aws dynamodb scan \
    --table-name MyTable \
    --endpoint-url http://localhost:4566 --region us-west-2 \
    --query 'Items | sort_by(@, &timestamp) | reverse(@)[:10]'
```
The reverse(@)[:10] gets the last 10 items.

## boto3 queries

### Query with sorting (assuming timestamp exists)
response = table.query(
    KeyConditionExpression="partitionKey = :pk",
    ExpressionAttributeValues={":pk": "someValue"},
    ScanIndexForward=False,  # Fetch latest records first
    Limit=10
)
### Print results
for item in response['Items']:
    print(item)







