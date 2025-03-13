from playwright.sync_api import sync_playwright
import time

# Define the dynamic selector for the content div
selector = "div.field.field-name-body.field-type-text-with-summary.field-label-hidden"

def scroll_page(page):
    """Scrolls down in steps to load more content."""
    for _ in range(3):  # Scroll in 3 steps for a smooth effect
        page.evaluate("window.scrollBy(0, window.innerHeight / 2)")  # Scroll half a page
        time.sleep(1)  # Wait a bit to let content load

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # Open browser visibly
    page = browser.new_page()
    page.goto("https://www.girlschase.com/article/why-does-stuff-work-girls-girls-swear-wouldnt")
    
    # Scroll the page down to load content
    scroll_page(page)
    
    # Wait until the target element is loaded
    page.wait_for_selector(selector, timeout=25000)
    
    # Extract the inner text of the matching element
    content = page.inner_text(selector)
    
    print("Page Title:", page.title())
    print("Content from the div:")
    print(content)
    
    browser.close()