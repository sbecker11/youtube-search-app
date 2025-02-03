# pylint: disable=W1203 # Use lazy % formatting in logging functions

import json
import logging
import os
import time

import schedule
from dotenv import load_dotenv

from youtube_query import YouTubeQuery

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeQueryScanner:
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is not set")
        self.config_url = os.getenv('CONFIG_URL', 'http://example.com/config.json')
        self.endpoint_url = os.getenv('ENDPOINT_URL', 'http://localhost:4566')  # Default to 'http://localhost:4566' if not set
        self.config_file = 'youtube_query_scanner_config.json'
        self.config = self.load_config(self.config_file)
        self.engine = YouTubeQuery()

    def load_config(self, config_file):
        with open(config_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    def run_queries(self, queries):
        for query in queries:
            try:
                subject = query['subject']
                logger.info(f"Starting query subject: {subject}")
                self.engine.search( subject=query['subject'])
                logger.info(f"Finished query subject: {subject}")

            except ValueError as error:
                print(f"Error running query {query['query']}: {error}")

    def schedule_queries(self):
        queries = self.config['queries']
        interval = self.config['schedule']['interval']
        time_of_day = self.config['schedule'].get('time', '10:00')

        if interval == 'hour':
            schedule.every().hour.do(self.run_queries, queries)
        elif interval == 'day':
            schedule.every().day.at(time_of_day).do(self.run_queries, queries)
        else:
            raise ValueError(f"Invalid interval value: {interval}. Must be 'hour' or 'day'.")

    def start(self):
        self.schedule_queries()
        while True:
            schedule.run_pending()
            time.sleep(10)

def main():
    """
    Main function to initialize the YouTubeQueryScanner and start it.
    """
    scanner = YouTubeQueryScanner()
    scanner.start()

if __name__ == '__main__':
    main()
