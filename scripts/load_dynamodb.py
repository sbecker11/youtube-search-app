import argparse
import sys
import os

# Add the src directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from youtube_table import YouTubeTable

def main():
    parser = argparse.ArgumentParser(description='Load data into DynamoDB table from a JSON file.')
    parser.add_argument('--table_name', type=str, default='loaded', help='Name of the new or existing DynamoDB table to load data into (default: loaded).')
    parser.add_argument('--json_file', type=str, default='dump.json', help='Path to the JSON file to load data from (default: dump.json)')

    args = parser.parse_args()

    print(f"Loading table: {args.table_name} from {args.json_file}")
    YouTubeTable.load_dbTable_from_json(args.table_name, args.json_file)

if __name__ == "__main__":
    main()
