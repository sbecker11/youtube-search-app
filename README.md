Overview

This docker-compose project creates a local-dynamodb image that runs in a localstack image on local DockerDesktop. Dockerfile and docker-compose.yml are used to deploy assets to DockerDesktop.

YouTubeQuery from youtube_query.py sends a variety of search queries to YouTubeMetadataAPI

Search query results are stored in DynamoDb tables using DynamoPersistenceEngine from dynamo_persistence_engine.py

RestApi from rest_api.py, uses FastAPI . The OpenAI documentation will be created in a local docs folder and it will be used to investigate the search query results stored in dynamodb.

Credentials for YouTube and AWS are stored in a local .env file, which is never uploaded to the remote github repo.

Docker configuration files are found at project root. Python source modules are found at project root. Pytest modules are found in /tests OpenAPI documentation files are found in /docs.

important links:
sssss


Architecture

dynamodb engine
  creates table definitions
  using metadata

query parameters
youtube_query
  builds search_videos query using easy_api_wrapper
  submits query request to YouTubeMetadataApi
  search videos response
  dynamodb engine saves data to tables













## YouTube Open AI Specification

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

