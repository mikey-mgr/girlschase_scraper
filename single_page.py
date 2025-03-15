import json
import os
import sys
from playwright.sync_api import sync_playwright

# Hardcoded URL to scrape
ARTICLE_URL = "https://www.girlschase.com/content/29-things-make-woman-resist-or-rebuff-you"  # Change this to your target URL
OUTPUT_FILE = "single_article.json"
MAX_RETRIES = 3  # Number of retries for fetching content

def reset_session(context):
    """Clears cookies and resets session storage."""
    context.clear_cookies()

def save_article(data):
    """Appends new article data to single_article.json if it exists; otherwise, creates a new file."""
    existing_articles = []

    # Load existing data if the file exists
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
                if not isinstance(existing_articles, list):
                    existing_articles = []  # Ensure it's a list
        except json.JSONDecodeError:
            print("⚠️ Warning: JSON file was corrupted. Starting fresh.")

    # Append the new article
    existing_articles.append(data)

    # Save updated list
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_articles, f, ensure_ascii=False, indent=2)
        print(f"✅ Article appended to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving article: {e}")


def scrape_article(url, page, context):
    """
    Scrapes content from a single article.
    Handles retries if content is incomplete.
    """
    content_selector = "div.field.field-name-body.field-type-text-with-summary.field-label-hidden"
    content = None

    for attempt in range(MAX_RETRIES):
        try:
            print(f"🕵️ Visiting: {url} (Attempt {attempt+1})")
            page.goto(url, timeout=30000)
            page.wait_for_selector(content_selector, timeout=10000)
            content = page.query_selector(content_selector).inner_text()
        except Exception as e:
            print(f"❌ Error loading page: {e}")
            reset_session(context)
            choice = input("Enter 'r' to retry or 'q' to quit: ").strip().lower()
            if choice == 'q':
                sys.exit(1)
            continue

        if "Read Full Story" not in content:
            break  # Exit retry loop if full content is retrieved
        else:
            print(f"⚠️ Incomplete content detected. Retrying...")
            reset_session(context)

    if content:
        title = page.title()
        return {"Title": title, "url": url, "content": content}
    else:
        print("❌ Failed to retrieve complete content.")
        return None

def main():
    """Main execution function."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False to see the browser in action
        context = browser.new_context()

        # Block non-essential resources to speed up scraping
        context.route("**/*", lambda route, request: 
                      route.abort() if request.resource_type in ["image", "stylesheet", "font"] else route.continue_())

        page = context.new_page()

        article_data = scrape_article(ARTICLE_URL, page, context)
        if article_data:
            save_article(article_data)

        browser.close()

if __name__ == "__main__":
    main()
