import sys
import json
from playwright.sync_api import sync_playwright

def reset_session(context):
    """
    Clears cookies and storage to reset the session.
    """
    context.clear_cookies()

def scrape_article(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=False for visible browsing
        context = browser.new_context()

        # Block non-essential resources like images, styles, and fonts
        context.route("**/*", lambda route, request: 
            route.abort() if request.resource_type in ["image", "stylesheet", "font"] else route.continue_()
        )

        page = context.new_page()

        max_retries = 3  # Number of retries
        for attempt in range(max_retries):
            page.goto(url, timeout=25000)

            # Wait for the target text to load
            selector = "div.field.field-name-body.field-type-text-with-summary.field-label-hidden"
            page.wait_for_selector(selector)  # Ensures the target text container is loaded

            # Extract content
            content = page.query_selector(selector).inner_text()

            # Check if the content includes "Read Full Story"
            if "Read Full Story" not in content:
                break  # Exit loop if full content is retrieved

            # If placeholder detected, reset session and retry
            print(f"Attempt {attempt + 1}: Detected limited content. Resetting session...")
            reset_session(context)

        # Get title
        title = page.title()

        # Print results in JSON format
        try:
            print(json.dumps({"Title": title, "url": url, "content": content}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
            sys.exit(1)

        browser.close()

if __name__ == "__main__":
    scrape_article(sys.argv[1])
