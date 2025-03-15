import sys
import json
import os

PRIMARY_FILE = "articles.json"

def load_articles(filename):
    """
    Loads articles from a given JSON file.
    Expects the file to contain a list of article objects.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Warning: {filename} does not contain a list of articles. Skipping.")
                return []
            return data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def merge_articles(primary_articles, new_articles):
    """
    Merges two lists of articles using the URL as the unique key.
    For duplicate URLs, keeps the article with the longer 'content' field.
    """
    # Create a dictionary keyed by URL with the best (most complete) article.
    articles_by_url = {}

    # First, load articles from primary_articles
    for article in primary_articles:
        url = article.get("url")
        if url:
            articles_by_url[url] = article

    # Now, merge new_articles: compare content length if duplicate URL is found.
    for article in new_articles:
        url = article.get("url")
        if not url:
            continue
        if url in articles_by_url:
            existing = articles_by_url[url]
            # Keep the one with the longer content field.
            if len(article.get("content", "")) > len(existing.get("content", "")):
                articles_by_url[url] = article
        else:
            articles_by_url[url] = article

    return list(articles_by_url.values())

def main():
    """
    Merges one or more JSON files into PRIMARY_FILE (articles.json).
    Usage: python merge_articles.py file1.json [file2.json ...]
    """
    if len(sys.argv) < 2:
        print("Usage: python merge_articles.py <file1.json> [file2.json ...]")
        sys.exit(1)

    # Load articles from the primary file if it exists.
    if os.path.exists(PRIMARY_FILE):
        primary_articles = load_articles(PRIMARY_FILE)
        print(f"Loaded {len(primary_articles)} articles from {PRIMARY_FILE}.")
    else:
        primary_articles = []

    # Merge articles from the provided files.
    for filename in sys.argv[1:]:
        # Skip merging if the filename is the primary file.
        if filename == PRIMARY_FILE:
            continue
        print(f"Merging articles from {filename}...")
        new_articles = load_articles(filename)
        primary_articles = merge_articles(primary_articles, new_articles)

    # Save the merged articles back to the primary file.
    try:
        with open(PRIMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(primary_articles, f, ensure_ascii=False, indent=2)
        print(f"✅ Successfully merged articles into {PRIMARY_FILE}. Total unique articles: {len(primary_articles)}")
    except Exception as e:
        print(f"Error saving merged articles: {e}")

if __name__ == "__main__":
    main()
