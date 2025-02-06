# pylint: disable=W1203 # Use lazy % formatting in logging functions

import json
import logging
import os
import time
from datetime import datetime
import croniter
from dotenv import load_dotenv

from youtube_query import YouTubeQuery, YouTubeQueryException

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_queries_per_scan = int(os.getenv("MAX_QUERIES_PER_SCAN", "10"))
class YouTubeQueryScannerException(Exception):
    pass

class YouTubeQueryScanner:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(YouTubeQueryScanner, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def get_singleton(cls):
        return cls._instance
    def __init__(self):
        if not hasattr(self, 'initialized'): # ensure that heavy initlalization happens only once
            self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
            if not self.youtube_api_key:
                raise ValueError("YOUTUBE_API_KEY environment variable is not set")
            self.config = self.load_json_file(os.getenv('QUERY_SCANNER_CONFIG_PATH', 'undefined'))
            self.query_engine = YouTubeQuery()
            self.run_status = "Ready"
            self.initialized = True  # Flag to show initialization has been done

    def load_json_file(self, json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)

    def run_queries(self, queries):
        if len(queries) > max_queries_per_scan:
            raise YouTubeQueryScannerException("num queries: %d exceeds configured \
                max_queries_per_scan:%d" % (len(queries), max_queries_per_scan))
        for query in queries:
            try:
                logger.info(f"Starting query: {query}")
                self.query_engine.search(query)
                logger.info(f"Finished query: {query}")
            except YouTubeQueryException as error:
                logger.error("Error running query: %s %s", query, {error})
                raise error

    def get_run_status(self):
        return self.run_status


    def set_run_status(self,run_status):
        self.run_status = run_status


    def start(self):
        """ Start running the schedule that calls run_queries
            according to the configured cron schedule.
            All times are tracked in utc timezone.
        """
        queries = self.config['queries']
        cron_string = self.config('cron_string')
        cron = croniter.croniter(cron_string, datetime.utcnow())
        next_execution = cron.get_next(datetime.utfnow())
        self.set_run_status("Running")
        while self.get_run_status() != "Stopped":
            utfnow = datetime.utfnow()
            if utfnow >= next_execution:
                self.run_queries(queries)
                next_execution = cron.get_next(datetime.utfnow())
            time.sleep(10)  # Sleep to prevent high CPU usage

def main():
    """
    Main function to initialize the YouTubeQueryScanner and start it.
    """
    scanner = YouTubeQueryScanner.get_singleton()
    scanner.start()
    logger.info("started")
    time.sleep(10)
    scanner.set_run_status("Stopped")
    logger.info("stopped")

if __name__ == '__main__':
    main()
