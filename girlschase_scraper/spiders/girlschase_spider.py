import scrapy
import logging
import subprocess
import json
import os

logging.getLogger('scrapy').setLevel(logging.DEBUG)

class GirlsChaseSpider(scrapy.Spider):
    name = "girlschase"
    custom_settings = {
        "FEED_FORMAT": "json",
        "FEED_URI": "articles.json",
        "FEED_EXPORT_ENCODING": "utf-8",
        "FEED_EXPORT_INDENT": 2,
        "FEED_STORE_EMPTY": False,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.25,
        "LOG_LEVEL": "DEBUG",
        "RETRY_TIMES": 5,
        "DOWNLOAD_TIMEOUT": 25,
    }

    def __init__(self, start_page=None, end_page=None, specific_page=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page) if start_page else 1
        self.end_page = int(end_page) if end_page else None
        self.specific_page = int(specific_page) if specific_page else None
        self.processed_urls = set()
        self.load_processed_urls()

    def load_processed_urls(self):
        """
        Load already-scraped URLs from articles.json to skip duplicates.
        """
        if os.path.exists("articles.json"):
            try:
                with open("articles.json", "r", encoding="utf-8") as f:
                    articles = json.load(f)
                    self.processed_urls = {article["url"] for article in articles}
                    self.logger.info(f"Loaded {len(self.processed_urls)} processed URLs.")
            except json.JSONDecodeError:
                self.logger.warning("articles.json is malformed. Skipping URL loading.")
                self.processed_urls = set()

    def save_processed_urls(self):
        """
        Save processed URLs back to articles.json safely.
        """
        temp_file = "articles_temp.json"

        try:
            # Write to a temporary file first
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(
                    [{"url": url} for url in self.processed_urls],
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            # Replace the original file with the temp file
            os.replace(temp_file, "articles.json")

        except Exception as e:
            self.logger.error(f"Failed to save processed URLs: {e}")

    def start_requests(self):
        """
        Dynamically generate URLs based on user input for scraping.
        """
        base_url = "https://www.girlschase.com/insights?redirect=/newmax.click&page="

        if self.specific_page:
            # Scrape only a specific page
            url = f"{base_url}{self.specific_page}"
            yield scrapy.Request(url=url, callback=self.parse)
        else:
            # Scrape a range of pages
            end_page = self.end_page if self.end_page else self.start_page
            for page_number in range(self.start_page, end_page + 1):
                url = f"{base_url}{page_number}"
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        """
        Extract article links and check if already processed.
        """
        article_links = response.css("h2 a::attr(href)").getall()

        for link in article_links:
            full_url = response.urljoin(link)

            # Skip duplicate URLs
            if full_url in self.processed_urls:
                self.logger.info(f"Skipping already processed URL: {full_url}")
                continue

            yield scrapy.Request(full_url, callback=self.parse_article)

    def parse_article(self, response):
        """
        Scrape article content via Playwright subprocess.
        """
        try:
            result = subprocess.run(
                ["python", "playwright_task.py", response.url],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                yield data

                # Add URL to processed list and save incrementally
                self.processed_urls.add(response.url)
                self.save_processed_urls()
            else:
                self.logger.error(f"Subprocess failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
