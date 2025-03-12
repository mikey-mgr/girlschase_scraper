import scrapy
import logging

logging.getLogger('scrapy').setLevel(logging.WARNING)  # Reduce logging

class GirlsChaseSpider(scrapy.Spider):
    name = "girlschase"
    custom_settings = {
        "FEED_FORMAT": "json",
        "FEED_URI": "articles.json",
        "FEED_EXPORT_ENCODING": "utf-8",
        "FEED_EXPORT_INDENT": 2,
        "FEED_STORE_EMPTY": False,
        "CONCURRENT_REQUESTS": 32,
        "DOWNLOAD_DELAY": 0.25,
        "LOG_LEVEL": "WARNING",
    }

    start_urls = ["https://www.girlschase.com/insights"]

    def parse(self, response):
        """Extract article links and follow pagination."""
        
        # Extract article links from h2 > a
        article_links = response.css("h2 a::attr(href)").getall()

        for link in article_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, callback=self.parse_article)

        # Follow next page
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_article(self, response):
        """Extract article content."""
        
        title = response.css("h1::text").get(default="No Title").strip()
        content = " ".join(response.css("div.field-items p::text").getall()).strip()

        yield {
            "title": title,
            "url": response.url,
            "content": content,
        }
