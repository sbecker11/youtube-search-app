import sys
import os

# Add the src directory to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from youtube.youtube_searcher_app import YouTubeSearcherApp

def main():
    YouTubeSearcherApp.main()

if __name__ == "__main__":
    main()
