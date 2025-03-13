import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.DEBUG)

def scrape_girlschase(max_pages=5):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.girlschase.com/insights")

        current_page = 1

        while current_page <= max_pages:
            # Extract article links and titles
            article_links = page.locator("h2 a").all()
            for article in article_links:
                link = article.get_attribute("href")
                title = article.inner_text()
                full_url = page.url + link
                print({"link": full_url, "title": title})

            # Check for next page link
            next_page = page.locator("li.next a").first
            if next_page.is_visible():
                next_page_url = next_page.get_attribute("href")
                page.goto(next_page_url)
                current_page += 1
            else:
                break

        browser.close()

if __name__ == "__main__":
    scrape_girlschase(max_pages=5)