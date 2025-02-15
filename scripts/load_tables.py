import argparse
from src.youtube_table import YouTubeTable
from src.youtube_storage import YouTubeStorage

def main():
    parser = argparse.ArgumentParser(description="Load YouTube tables from a JSON file.")
    parser.add_argument('json_file_path', type=str, nargs='?', help='The path to the JSON file where the tables will be loaded.')
    args = parser.parse_args()

    if not args.json_file_path:
        print("Usage: python load_tables.py <json_file_path>")
        return

    YouTubeStorage.get_singleton().load_tables(args.json_file_path)

if __name__ == "__main__":
    main()

