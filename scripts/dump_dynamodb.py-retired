import argparse
import sys
import os

# Add the src directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from youtube_table import YouTubeTable

def main():
    parser = argparse.ArgumentParser(description='Dump DynamoDB table.')
    parser.add_argument('table_name', type=str, help='The name of the existing DynamoDB table to dump data from')
    parser.add_argument('--json_file_path', type=str, default='dump.json', help='Path to the json file to dump into (default: dump.json)')
    args = parser.parse_args()

    table_name = args.table_name
    json_file_path = args.json_file_path
    print(f"Dumping table: {table_name} to {json_file_path}")
    # Call the function to dump the table
    YouTubeTable.dump_dbTable_to_json(table_name, json_file_path)

if __name__ == "__main__":
    main()
