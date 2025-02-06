# Overview of the YouTube Search API project

This docker-compose project creates a local-dynamodb image that runs in a localstack image on local DockerDesktop. `Dockerfile` and `docker-compose.yaml` reside at project-root, and are used to deploy assets to DockerDesktop.

QueryEngine in `src/query_engine.py` sends a variety of RESTful search queries to the YouTubeMetadataAPI. Query request and response data access operations are handled by the YouTubeStorage object. Example query response data may be found in /data/query_response_head.json and query_response_item.json

Search query requests and responses are stored in the Responses dynamoDb tables by YouTubeStorage in `src/youtube_storage.py`. Each response record has a unique primary key named `response_id`. All snippets associated with a response are stored in a Snippets table and refer to foreign key `response_id`. Dyanamo table definitions for these tables reside at `/data/responses_table_config.json` and `/data/snippets_data_config.json`

YouTubStoreageApi from `src/youtube_storage_api.py` uses FastAPI to handle queries made against YouTubeStorage. OpenAI documentation is created during `docker-compose up --build` and resides at `/docs`.

QueryScanner in `src/query_scanner.py` ses croniter and schedule to run a batch of queries to the YouTubeAPI via QueryEngine.

Credentials for YouTube and AWS are stored in a local `.env` file, which is never uploaded to the remote github repo.

The structure of the `.env` file is:

```text
YOUTUBE_API_KEY=*****
AWS_ACCESS_KEY_ID=*****
AWS_DEFAULT_REGION=us-west-2
PYTHONPATH=src:tests
DYNAMODB_URL=http://localstack:4566
RESPONSES_CONFIG_PATH=./data/responses_table_config.json
SNIPPETS_CONFIG_PATH=./data/snippets_table_config.json
QUERY_SCANNER_CONFIG_PATH=./data/query_scanner_config.json
MAX_QUERIES_PER_SCAN=100
```

Docker configuration files are found at project root. Python source modules are found at project root under the `src` directory. Pytest modules are found in `/tests` OpenAPI documentation files are found in `/docs`.

important links:
http://localhost:8000 link to the YouTubeStorageApi

Project Structure:
```tree
├── Dockerfile
├── README.md
├── constraints.txt
├── data
│   ├── query_response_head.json
│   ├── query_response_item.json
│   ├── query_scanner_config.json
│   ├── responses_table_config.json
│   └── snippets_table_config.json
├── dist
│   └── youtube-search-api.egg-info
│       ├── PKG-INFO
│       ├── SOURCES.txt
│       ├── dependency_links.txt
│       └── top_level.txt
├── docker-compose.yaml
├── jest.config.js
├── localstack.pid
├── requirements.txt
├── scripts
│   └── run-pytest
├── src
│   ├── __init__.py
│   ├── query_engine.py
│   ├── query_scanner.py
│   ├── youtube_storage.py
│   ├── youtube_storage_api.py
│   └── youtube_table.py
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
`docker compose up --build`

### Run scanner command
```
APP_CONTAINER_ID=$(docker ps | grep "youtube-search-api-app" | awk '{print $1}')
echo "$APP_CONTAINER_ID"
docker exec -it $APP_CONTAINER_ID python run_scanner.py
```

### API Endpoints
`http://localhost:5000/headers` Endpoint to query the query headers stored in dynamodb
`http://localhost:5000/items` Endpoint to query the items stored in dynamodb


### API Documentation
`http://localhost:5000/docs` Swagger UI to access the interactive Swagger UI documentation
`http://localhost:5000/redoc` ReDoc to access the clean and readable ReDoc documentation

