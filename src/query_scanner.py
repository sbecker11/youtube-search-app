# pylint: disable=C0209 # Use lazy % formatting in logging functions

import logging
import os
import time
from datetime import datetime
from typing import Dict

import croniter
from dotenv import load_dotenv
from query_engine import QueryEngine, QueryEngineException

from dynamodb_utils.json_utils import DynamoDbJsonUtils
# global app run mode
APP_RUN_MODES = DynamoDbJsonUtils.load_json_file("APP_RUN_MODES.json")

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_queries_per_scan = int(os.getenv("MAX_QUERIES_PER_SCAN", "10"))

# set this to true to skip query_engine setup during ininitialization

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

        self.config = DynamoDbJsonUtils.load_json_file(os.getenv('QUERY_SCANNER_CONFIG_PATH', 'undefined'))
        if not isinstance(self.config, dict):
            raise RuntimeError("config file not loaded")
        if not self.get_queries():
            raise RuntimeError("queries not found in config")
        if not self.get_cron_string():
            raise RuntimeError("cron_string not found in config file")

        logger.info("the QueryScanner instance initialized with validated config")

        if APP_RUN_MODES["USE_SCANNER"] != "yes" or APP_RUN_MODES["SEND_YOUTUBE_QUERIES"] != "yes":
            logger.warning("APP_RUN_MODES['USE_SCANNER'] is '%s'", APP_RUN_MODES['USE_SCANNER'])
            logger.warning("APP_RUN_MODES['SEND_YOUTUBE_QUERIES'] is '%s'", APP_RUN_MODES['SEND_YOUTUBE_QUERIES'])
            logger.warning("the QueryScanner instance HAS NOT BEEN INITIALIZED with the QueryEngine instance")
        else:
            self.query_engine = QueryEngine.get_singleton()
            logger.info("the QueryScanner instance initialized with the QueryEngine instance")

        self.run_status = "Ready"
        logger.info("the QueryScanner instance initialized with run_status: %s", self.run_status)

        self.initialized = True  # Flag to show heavy initialization has been done

    def validate_config(self, config:Dict):
        """ validate the contents of the json config file """
        if not config.get("queries"):
            raise QueryScannerException("empty list of queries")
        if len(config["queries"]) > max_queries_per_scan:
            raise QueryScannerException("number of listed queries exceeds max_queries")
        cron_string = config.get("cron-string")
        if not cron_string or not croniter.croniter.is_valid(cron_string):
            raise QueryScannerException("cron-string does not match the required pattern")

    def run_queries(self, queries):
        """ call the query_engine to search on the give list queries
            that are not necessarily in the config.
        """
        if len(queries) > max_queries_per_scan:
            raise QueryScannerException("num queries: %d exceeds configured \
                max_queries_per_scan: %d" % (len(queries), max_queries_per_scan))
        for query in queries:
            try:
                logger.info("Starting query %s:", {query})
                self.query_engine.search(query)
                logger.info("Finished query:%s", {query})
            except QueryEngineException as error:
                logger.error("Error running query: %s %s", query, {error})
                raise error

    def get_run_status(self):
        return self.run_status

    def set_run_status(self, run_status):
        self.run_status = run_status
        logger.info("run_status set to %s", self.run_status)

    def get_cron_string(self):
        """ return the cron_string from the config """
        return self.config['cron-string']

    def get_queries(self):
        """ return the queries list from the config """
        return self.config['queries']

    def run_once(self, listener=None):
        """ Execute run the queries search one time
            and invoke the given listener if defined
        """
        try:
            self.run_queries(self.get_queries())
            if listener:
                listener()
        except QueryEngineException as error:
            if "API key expired" in str(error):
                logger.info("API key expired")
            else:
                logger.info("scanner.run_once failed with error:%s", {error})
            raise error

    def start(self):
        """ Start running the schedule that calls run_queries
            according to the configured cron schedule.
            All times are tracked in utc timezone.
        """
        cron_string = self.get_cron_string()
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
                try:
                    self.run_queries(self.get_queries())
                except QueryEngineException as error:
                    logger.info("scanner.run_queries failed with error:%s", {error})
                next_execution = cron.get_next(datetime)
                logger.info("next execution scheduled for %s", next_execution.isoformat())
            time.sleep(10)  # Sleep to prevent high CPU usage

def main():
    scanner = QueryScanner.get_singleton()

    logger.info("QueryScanner running queries:")
    for query in scanner.get_queries():
        logger.info(query)

    scanner.run_once(None)

if __name__ == '__main__':
    main()
