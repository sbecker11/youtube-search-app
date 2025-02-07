# pylint: disable=W1203 # Use lazy % formatting in logging functions

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict

import croniter
from dotenv import load_dotenv

from query_engine import QueryEngine, QueryEngineException

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_queries_per_scan = int(os.getenv("MAX_QUERIES_PER_SCAN", "10"))

class QueryScannerException(Exception):
    pass

class QueryScanner:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # Only pass the class, no additional args
        return cls._instance

    @classmethod
    def get_singleton(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_singleton(cls):
        cls._instance = None

    def __init__(self):

        if not hasattr(self, 'initialized'):
            self.initialized = False  # singleton logic to ensure that heavy initialization is done only once
        elif self.initialized:
            return

        self.config = self.load_json_file(os.getenv('QUERY_SCANNER_CONFIG_PATH', 'undefined'))
        if not isinstance(self.config, dict):
            raise RuntimeError("config file not loaded")
        logger.info("the QueryScanner instance config loaded")

        self.run_status = "Ready"
        logger.info("the QueryScanner instance run_status:%s", self.run_status)

        self.query_engine = QueryEngine.get_singleton()
        logger.info("the QueryScanner instance initialized with the QueryEngine instance")

        logger.info("the QueryScanner instance has started")
        self.start()
        self.initialized = True  # Flag to show heavy initialization has been done

    def load_json_file(self, json_file_path):
        """ raised exceptions FileNotFoundError, JSONDecodeError """
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)

    def validate_config(self, config:Dict):
        if not config.get("queries"):
            raise QueryScannerException("empty list of queries")
        if len(config["queries"]) > max_queries_per_scan:
            raise QueryScannerException("number of listed queries exceeds max_queries")
        cron_string = config.get("cron-string")
        if not cron_string or not croniter.croniter.is_valid(cron_string):
            raise QueryScannerException("cron-string does not match the required pattern")

    def run_queries(self, queries):
        if len(queries) > max_queries_per_scan:
            raise QueryScannerException("num queries: %d exceeds configured \
                max_queries_per_scan:%d" % (len(queries), max_queries_per_scan))
        for query in queries:
            try:
                logger.info(f"Starting query: {query}")
                self.query_engine.search(query)
                logger.info(f"Finished query: {query}")
            except QueryEngineException as error:
                logger.error("Error running query: %s %s", query, {error})
                raise error

    def get_run_status(self):
        return self.run_status

    def set_run_status(self, run_status):
        self.run_status = run_status
        logger.info("run_status set to %s", self.run_status)

    def start(self):
        """ Start running the schedule that calls run_queries
            according to the configured cron schedule.
            All times are tracked in utc timezone.
        """
        queries = self.config['queries']
        cron_string = self.config['cron-string']
        logger.info("cron_string: %s", cron_string)
        cron = croniter.croniter(cron_string, datetime.utcnow())
        next_execution = cron.get_next(datetime)
        logger.info("*" * 80)
        logger.info("first execution scheduled for %s", next_execution.isoformat())
        self.set_run_status("Running")
        while self.get_run_status() != "Stopped":
            utcnow = datetime.utcnow()
            if utcnow >= next_execution:
                logger.info("*" * 80)
                logger.info("execution starting at %s", utcnow.isoformat())
                self.run_queries(queries)
                next_execution = cron.get_next(datetime)
                logger.info("next execution scheduled for %s", next_execution.isoformat())
            time.sleep(10)  # Sleep to prevent high CPU usage

def main():
    logger.info("QueryScanner says hello")

if __name__ == '__main__':
    main()
