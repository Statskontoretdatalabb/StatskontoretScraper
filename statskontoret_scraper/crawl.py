from __future__ import annotations

from pathlib import Path

from scrapy.crawler import CrawlerProcess

from statskontoret_scraper.config import SourceConfig, get_source, load_sources
from statskontoret_scraper.models import RawPage
from statskontoret_scraper.spiders import ForumSpider, StatskontoretSpider


class CollectItemsPipeline:
    items: list[dict[str, str | None]] = []

    def process_item(self, item):
        self.items.append(dict(item))
        return item


def _settings() -> dict[str, object]:
    return {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": True,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "ITEM_PIPELINES": {
            "statskontoret_scraper.crawl.CollectItemsPipeline": 100,
        },
    }


def _spider_for_source(source: SourceConfig):
    if source.kind == "sitemap":
        return StatskontoretSpider
    if source.kind == "seeded":
        return ForumSpider
    raise ValueError(f"Unsupported source kind: {source.kind}")


def crawl_sources(source_names: list[str] | None = None) -> list[RawPage]:
    sources = (
        [get_source(name) for name in source_names]
        if source_names
        else load_sources()
    )

    CollectItemsPipeline.items = []
    process = CrawlerProcess(_settings())
    for source in sources:
        process.crawl(_spider_for_source(source), source=source)
    process.start()

    return [
        RawPage(
            page_id=item["page_id"],
            source_system=item["source_system"],
            source_url=item["source_url"],
            title=item["title"],
            markdown_content=item["markdown_content"],
            plain_text_content=item["plain_text_content"],
            updated_at=item["updated_at"],
            content_hash=item["content_hash"],
        )
        for item in CollectItemsPipeline.items
    ]


def default_output_dir() -> Path:
    return Path("build/latest")
