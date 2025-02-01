import json
import schedule
import time
import os
from youtube_query_engine import YouTubeQueryEngine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY environment variable is not set")
CONFIG_URL = os.getenv('CONFIG_URL', 'http://example.com/config.json')
ENDPOINT_URL = os.getenv('ENDPOINT_URL', 'http://localhost:4566')  # Default to 'http://localhost:4566' if not set

def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as file:
        return json.load(file)

def run_queries(engine, queries):
    for query in queries:
        try:
            engine.search(query['query'], query['subject'])
        except ValueError as error:
            print(f"Error running query {query['query']}: {error}")

def schedule_queries(engine, config):
    queries = config['queries']
    interval = config['schedule']['interval']
    time_of_day = config['schedule'].get('time', '10:00')

    if interval == 'hour':
        schedule.every().hour.do(run_queries, engine, queries)
    elif interval == 'day':
        schedule.every().day.at(time_of_day).do(run_queries, engine, queries)
    else:
        raise ValueError(f"Invalid interval value: {interval}. Must be 'hour' or 'day'.")

def main():
    """
    Main function to load configuration, initialize the YouTubeQueryEngine,
    schedule queries, and run the scheduler indefinitely.
    """
    config_file = 'query_scanner_config.json'
    config = load_config(config_file)
    engine = YouTubeQueryEngine(YOUTUBE_API_KEY, config_url=CONFIG_URL, endpoint_url=ENDPOINT_URL)
    schedule_queries(engine, config)

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == '__main__':
    main()
