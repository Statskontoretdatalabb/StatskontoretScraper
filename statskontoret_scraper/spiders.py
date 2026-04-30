from __future__ import annotations

from typing import Iterable

import scrapy
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import Sitemap

from statskontoret_scraper.config import SourceConfig
from statskontoret_scraper.normalize import build_raw_page


class BasePageSpider:
    source: SourceConfig

    def should_skip(self, url: str) -> bool:
        return any(url.startswith(prefix) for prefix in self.source.exclude_url_prefixes)

    def is_html(self, response: Response) -> bool:
        content_type = response.headers.get("Content-Type", b"").decode("latin-1")
        return "text/html" in content_type

    def parse_page(self, response: Response) -> dict[str, str | None] | None:
        if self.should_skip(response.url) or not self.is_html(response):
            return None
        try:
            page = build_raw_page(response, self.source)
        except ValueError:
            return None
        return page.to_dict()


class StatskontoretSpider(SitemapSpider, BasePageSpider):
    name = "statskontoret"

    def __init__(self, source: SourceConfig, *args, **kwargs):
        self.source = source
        self.allowed_domains = list(source.allowed_domains)
        self.sitemap_urls = list(source.start_urls)
        super().__init__(*args, **kwargs)

    def parse(self, response: Response, **kwargs):
        page = self.parse_page(response)
        if page:
            yield page

    def sitemap_filter(self, entries: Sitemap):
        for entry in entries:
            loc = entry.get("loc")
            if loc and not self.should_skip(loc):
                yield entry


class ForumSpider(scrapy.Spider, BasePageSpider):
    name = "forum"

    def __init__(self, source: SourceConfig, *args, **kwargs):
        self.source = source
        self.allowed_domains = list(source.allowed_domains)
        self.start_urls = list(source.start_urls)
        super().__init__(*args, **kwargs)

    async def start(self) -> Iterable[scrapy.Request]:
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response: Response):
        page = self.parse_page(response)
        if page:
            yield page

        for selector in self.source.link_selectors:
            for href in response.css(selector).getall():
                url = response.urljoin(href)
                if any(domain in url for domain in self.allowed_domains):
                    yield scrapy.Request(url, callback=self.parse)
