#!/usr/bin/env python3

import requests
import defusedxml.ElementTree as ET
import random
import os
import sys
from typing import List

def handle_error(message):
    """Print error message, wait for key press, and return 1."""
    print(message)
    input("Press any key to continue...")  # Python's equivalent to bash 'read -n 1'
    return 1

def fetch_random_latest_trends(prev_file="latest_trends.txt") -> List[str]:
    """Fetch 3 random trending topics from Google Trends, avoiding repeats."""
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    
    # Fetch the RSS feed
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for bad HTTP status
    except (requests.RequestException, TimeoutError) as e:
        return handle_error(f"Failed to fetch trends: {e}")
    
    # Parse XML and extract titles (up to 100)
    try:
        root = ET.fromstring(response.content)
        topics = [item.find("title").text for item in root.findall(".//item")][:100]
    except ET.ParseError:
        return handle_error("Failed to parse trends XML.")
    
    if not topics:
        return handle_error("No trends found.")
    
    # Load previous topics from file if it exists
    prev_topics = set()
    if os.path.exists(prev_file):
        with open(prev_file, "r", encoding="utf-8") as f:
            prev_topics = set(line.strip() for line in f if line.strip())
    
    # Filter out previously used topics
    filtered_topics = [t for t in topics if t not in prev_topics]
    if not filtered_topics:
        return handle_error("No new trends available after filtering.")
    
    # Pick 3 random topics
    selected = random.sample(filtered_topics, k=min(3, len(filtered_topics)))
    
    # Append new selections to the file
    with open(prev_file, "a", encoding="utf-8") as f:
        for topic in selected:
            f.write(f"{topic}\n")
    
    # Output the selected topics
    return selected

if __name__ == "__main__":
    print("Fetching 3 random trending topics from the top 100 (avoiding repeats)...")
    sys.exit(fetch_random_latest_trends("my_latest_trends.txt"))