#!/usr/bin/env python3
from youtube.youtube_searcher_app import YouTubeSearcherApp
def main():
    app = YouTubeSearcherApp.get_singleton()
    queries = app.list_queries()
    print(f"Found {len(queries)} queries")
    for query in queries:
        print(f"Query: {query}")

if __name__ == "__main__":
    main()
