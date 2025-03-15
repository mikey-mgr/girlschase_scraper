import sys
import json
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# Base URL for insights pages; page number will be appended.
DEFAULT_BASE_URL = "https://www.girlschase.com/insights?redirect=/newmax.click&page="
OUTPUT_FILE = "articles.json"  # Primary file to store articles
MAX_RETRIES = 3  # Number of retries per article if content is incomplete

def reset_session(context):
    """Clears cookies and storage for the current context."""
    context.clear_cookies()

def load_existing_articles():
    """
    Loads existing articles from OUTPUT_FILE.
    Returns a dictionary keyed by URL to avoid duplicates.
    """
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                articles = json.load(f)
                return {article["url"]: article for article in articles if "url" in article}
        except json.JSONDecodeError:
            print("❌ Warning: Existing articles file is corrupted. Starting fresh.")
    return {}

def save_articles(articles_dict):
    """
    Saves the articles dictionary (converted to a list) to OUTPUT_FILE.
    """
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(articles_dict.values()), f, ensure_ascii=False, indent=2)
        print(f"✅ Saved {len(articles_dict)} unique articles to {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Error saving articles: {e}")

def extract_article_links(page, base_url):
    """
    Extracts article links from the insights page.
    Uses the selector for <a> tags inside an <h2> element,
    and converts relative URLs to absolute using urljoin.
    """
    selector = "h2 a"
    links = [a.get_attribute("href") for a in page.query_selector_all(selector)]
    return [urljoin(base_url, link) for link in links if link]

def scrape_article(url, page, context):
    """
    Visits the article URL and scrapes its content.
    Retries up to MAX_RETRIES times if the scraped content is incomplete
    (i.e. contains the placeholder "Read Full Story").
    On error or if incomplete after MAX_RETRIES, prompts the user to retry, skip, or quit.
    Returns a dictionary with keys "Title", "url", and "content", or None if skipped.
    """
    content_selector = "div.field.field-name-body.field-type-text-with-summary.field-label-hidden"
    content = None

    for attempt in range(MAX_RETRIES):
        try:
            page.goto(url, timeout=30000)
            page.wait_for_selector(content_selector)
            content = page.query_selector(content_selector).inner_text()
        except Exception as e:
            print(f"❌ Error on attempt {attempt+1} for {url}: {e}")
            reset_session(context)
            choice = input("Enter 'r' to retry this article or 's' to skip: ")
            if choice.lower() == 's':
                return None
            else:
                continue

        if "Read Full Story" not in content:
            break
        else:
            print(f"Attempt {attempt+1}: Incomplete content detected. Resetting session and retrying...")
            reset_session(context)
    else:
        # After MAX_RETRIES, if content is still incomplete, prompt the user.
        while True:
            choice = input(f"Article {url} still appears incomplete after {MAX_RETRIES} attempts. "
                           "Enter 'r' to retry, 's' to skip, or 'q' to quit: ")
            if choice.lower() == 's':
                return None
            elif choice.lower() == 'q':
                print("Quitting. Saving scraped articles so far...")
                sys.exit(0)
            elif choice.lower() == 'r':
                print("Retrying article...")
                return scrape_article(url, page, context)
            else:
                print("Invalid input. Please enter 'r', 's', or 'q'.")

    title = page.title()
    return {"Title": title, "url": url, "content": content}

def main():
    """
    Main routine.
    Accepts command-line arguments to specify a single page or a range of pages.
    Usage examples:
      • python insights_base.py           # Processes page 1
      • python insights_base.py 5         # Processes only page 5
      • python insights_base.py 3 6       # Processes pages 3 through 6
    """
    args = sys.argv[1:]
    if len(args) == 0:
        pages = [1]  # Default: only page 1
    elif len(args) == 1:
        try:
            pages = [int(args[0])]
        except ValueError:
            print("Invalid page number provided.")
            sys.exit(1)
    else:
        try:
            start_page = int(args[0])
            end_page = int(args[1])
            pages = list(range(start_page, end_page + 1))
        except ValueError:
            print("Invalid page numbers provided.")
            sys.exit(1)

    # Load previously scraped articles (if any)
    articles_dict = load_existing_articles()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False for visible browsing
        context = browser.new_context()

        # Block non-essential resources to speed up scraping.
        context.route("**/*", lambda route, request:
                      route.abort() if request.resource_type in ["image", "stylesheet", "font"] else route.continue_())

        # Create a single page for navigating both insights and article pages.
        page = context.new_page()

        for num in pages:
            insight_url = f"{DEFAULT_BASE_URL}{num}"
            print(f"\n🔎 Processing insights page: {insight_url}")
            try:
                page.goto(insight_url, timeout=30000)
            except Exception as e:
                print(f"❌ Error loading insights page {insight_url}: {e}")
                continue

            # Extract article links from the insights page.
            article_links = extract_article_links(page, insight_url)
            print(f"➡️  Found {len(article_links)} article links on page {num}.")

            for art_url in article_links:
                if art_url in articles_dict:
                    print(f"⏩ Skipping already processed article: {art_url}")
                    continue

                print(f"📰 Scraping article: {art_url}")
                article_data = scrape_article(art_url, page, context)
                if article_data:
                    articles_dict[art_url] = article_data
                    save_articles(articles_dict)  # Save incrementally after each successful article

        browser.close()
    print("✅ Finished scraping all pages.")

if __name__ == "__main__":
    main()
