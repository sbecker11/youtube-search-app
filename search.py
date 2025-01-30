
# pylint: disable=C0111  # Missing module docstring
# pylint: disable=C0114  # Missing module docstring
# pylint: disable=C0116  # Missing function docstring

#!/usr/bin/python

# This sample executes a search request for the specified search term.
# Sample usage:
#   python search.py --q=surfing --max-results=10
# NOTE: To use the sample, you must provide a developer key obtained
#       in the Google APIs Console. Search for "REPLACE_ME" in this code
#       to find the correct place to provide that key..

import os
import json
import argparse
from dotenv import load_dotenv

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = API_KEY
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def youtube_search(options):
    youtube = build(
        YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY
    )

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = (
        youtube.search()
        .list(q=options.q, part="id,snippet", maxResults=options.max_results)
        .execute()
    )

    ### Response format:
    # https://developers.google.com/youtube/v3/docs/search/list
    # response: {
    #     "kind": "youtube#searchListResponse",
    #     "etag": etag,
    #     "nextPageToken": string,
    #     "prevPageToken": string,
    #     "regionCode": string,
    #     "pageInfo": {
    #         "totalResults": integer,
    #         "resultsPerPage": integer
    #     },
    #     "items": [
    #         search Resource
    #     ]
    # }

    print("search_response")
    print(json.dumps(search_response, indent=4))


    # for key, value in search_response.items():
    #     if key != "items":
    #         print(f"  {key}: {value}")
    #     else:
    #         items = value
    #         for item in items:
    #             print(f"item.id:{item['id']}")


    videos = []
    channels = []
    playlists = []

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append(
                f"{search_result['snippet']['title']} ({search_result['id']['videoId']})"
            )
        elif search_result["id"]["kind"] == "youtube#channel":
            channels.append(
                f"{search_result['snippet']['title']} ({search_result['id']['channelId']})"
            )
        elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append(
                f"{search_result['snippet']['title']} ({search_result['id']['playlistId']})"
            )

    print("Videos:\n", "\n".join(videos), "\n")
    print("Channels:\n", "\n".join(channels), "\n")
    print("Playlists:\n", "\n".join(playlists), "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--q", help="Search term", default="Google")
    parser.add_argument("--max-results", help="Max results", default=25)
    parser.add_argument("-lr", help="Search language", default="en")
    args = parser.parse_args()

    try:
        print()
        print(f"search args:{args}")
        print()
        youtube_search(args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
