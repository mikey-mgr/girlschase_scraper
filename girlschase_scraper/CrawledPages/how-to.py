import sys
import json
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

DEFAULT_URL = "https://www.girlschase.com/start-here"
OUTPUT_FILE = "how-to.json"  # File where articles will be saved
MAX_RETRIES = 3  # Maximum number of retries for incomplete articles

def reset_session(context):
    """
    Clears cookies and storage to reset the session.
    """
    context.clear_cookies()

def extract_article_links(page, base_url):
    """
    Extracts and converts article links from <a> tags inside <div class="how-to-container">
    into absolute URLs using urljoin().
    """
    selector = "div.how-to-container a"
    links = [a.get_attribute("href") for a in page.query_selector_all(selector)]
    return [urljoin(base_url, link) for link in links if link]

def load_existing_articles():
    """
    Loads existing articles from how-to.json to prevent duplicates.
    Returns a dict with URLs as keys.
    """
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
                return {article["url"]: article for article in existing_articles}
        except json.JSONDecodeError:
            print("❌ Error: how-to.json is corrupted. Starting fresh.")
    return {}

def save_articles(articles):
    """
    Saves the merged list of articles to how-to.json.
    """
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(articles.values()), f, ensure_ascii=False, indent=2)
        print(f"✅ Successfully saved {len(articles)} unique articles to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving articles: {str(e)}")

def scrape_articles_from_page(url):
    """
    Navigates to the given URL, extracts article links from the container,
    then navigates to each article link to scrape its content.
    Uses a retry loop to avoid saving incomplete articles.
    If a timeout or error occurs, prompts the user to retry or quit,
    saving any articles scraped so far.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        # Block non-essential resources (images, styles, fonts)
        context.route("**/*", lambda route, request:
            route.abort() if request.resource_type in ["image", "stylesheet", "font"] else route.continue_()
        )

        page = context.new_page()
        page.goto(url, timeout=30000)

        # Extract article links and ensure they're absolute URLs
        article_links = extract_article_links(page, url)
        print(f"🔗 Found {len(article_links)} article links.")

        # Load existing articles to avoid duplicates
        existing_articles = load_existing_articles()
        new_articles = {}

        # Selector for the article content
        content_selector = "div.field.field-name-body.field-type-text-with-summary.field-label-hidden"

        for article_url in article_links:
            if article_url in existing_articles:
                print(f"⏩ Skipping already scraped: {article_url}")
                continue

            print(f"📰 Scraping article: {article_url}")
            content = None
            article_success = False

            for attempt in range(MAX_RETRIES):
                try:
                    page.goto(article_url, timeout=30000)
                    page.wait_for_selector(content_selector)
                    content = page.query_selector(content_selector).inner_text()
                except Exception as e:
                    print(f"❌ Error on attempt {attempt+1} for {article_url}: {str(e)}")
                    reset_session(context)
                    choice = input("An error occurred. Enter 'r' to retry this article or 'q' to quit: ")
                    if choice.lower() == 'q':
                        print("Exiting. Saving scraped articles so far...")
                        existing_articles.update(new_articles)
                        save_articles(existing_articles)
                        browser.close()
                        sys.exit(0)
                    else:
                        continue

                # If the content is complete (doesn't include the placeholder text), exit the loop
                if "Read Full Story" not in content:
                    article_success = True
                    break
                else:
                    print(f"Attempt {attempt + 1}: Detected limited content. Resetting session...")
                    reset_session(context)

            if not article_success:
                print(f"❌ Skipping article (incomplete after {MAX_RETRIES} attempts): {article_url}")
                continue

            title = page.title()
            new_articles[article_url] = {
                "Title": title,
                "url": article_url,
                "content": content
            }

        # Merge new articles with existing ones and save
        existing_articles.update(new_articles)
        save_articles(existing_articles)
        browser.close()

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    scrape_articles_from_page(url)
