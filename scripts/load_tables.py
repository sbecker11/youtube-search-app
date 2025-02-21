import argparse
from youtube.youtube_storage import YouTubeStorage
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

default_table_storage_path = os.getenv("DEFAULT_TABLE_STORAGE_PATH")

def main():
    parser = argparse.ArgumentParser(description="Load YouTube tables from a JSON file.")
    parser.add_argument('json_file_path', type=str, nargs='?', default=default_table_storage_path, help='The path to the JSON file where the tables will be loaded.')
    args = parser.parse_args()

    if not args.json_file_path:
        print("Usage: python load_tables.py <json_file_path>")
        return

    YouTubeStorage.get_singleton().load_tables(args.json_file_path)

if __name__ == "__main__":
    main()

