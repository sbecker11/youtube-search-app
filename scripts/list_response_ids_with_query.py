#!/usr/bin/env python3
from youtube.youtube_searcher_app import YouTubeSearcherApp
import sys
def main():
    if len(sys.argv) < 2:
        print("Usage: list_requests_with_query.py <query>")
        sys.exit(1)
    queryValue = sys.argv[1]

    app = YouTubeSearcherApp.get_singleton()
    response_ids = app.list_response_ids_with_query(query_value=queryValue)
    print(f"Found {len(response_ids)} response_ids")
    for response_id in response_ids:
        print(f"response_id: {response_id}")

if __name__ == "__main__":
    main()
