#!/usr/bin/env python3
from youtube.youtube_searcher_app import YouTubeSearcherApp
import sys
def main():
    if len(sys.argv) < 2:
        print("Usage: list_snippets_with_response_id.py <response_id>")
        sys.exit(1)
    response_id = sys.argv[1]

    app = YouTubeSearcherApp.get_singleton()
    snippets = app.list_snippets_with_response_id(response_id=response_id)
    print(f"Found {len(snippets)} snippets")
    for snippet in snippets:
        best_size_key = None
        max_width = 0
        thumbnailSizes = ["default", "medium", "high", "standard", "maxres"]
        for thumbnailSize in thumbnailSizes:
            size_key = f"thumbnails.{thumbnailSize}."
            width_key = size_key + "width"
            url_key = size_key + "url"
            if width_key in snippet and url_key in snippet:
                if snippet[width_key] and snippet[url_key]:
                    width = int(snippet[width_key])
                    if width > max_width:
                        best_size_key = size_key
                        max_width = width

        if snippet['description']:
            print(f"channelTitle: {snippet['channelTitle']}")
            print(f"  description: {snippet['description']}")
            if best_size_key:
                print(f"    {best_size_key}url: {snippet[best_size_key + 'url']}")
                print(f"    {best_size_key}width: {snippet[best_size_key + 'width']}")


if __name__ == "__main__":
    main()
