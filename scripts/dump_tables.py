import argparse
from src.youtube_storage import YouTubeStorage

def main():
    parser = argparse.ArgumentParser(description="Dump YouTube tables to a JSON file.")
    parser.add_argument('json_file_path', type=str, nargs='?', help='The path to the JSON file where the tables will be dumped.')
    args = parser.parse_args()

    if not args.json_file_path:
        print("Usage: python dump_tables.py <json_file_path>")
        return

    YouTubeStorage.get_singleton().dump_tables(args.json_file_path)

if __name__ == "__main__":
    main()

