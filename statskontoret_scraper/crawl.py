from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess

from statskontoret_scraper.config import SourceConfig, get_source, load_sources
from statskontoret_scraper.ip_rotator import IpRotatorMiddleware
from statskontoret_scraper.models import RawPage
from statskontoret_scraper.spiders import ForumSpider, StatskontoretSpider


class CollectItemsPipeline:
    items: list[dict[str, str | None]] = []

    def process_item(self, item):
        self.items.append(dict(item))
        return item


def _settings(sources: list[SourceConfig]) -> dict[str, object]:
    settings: dict[str, object] = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": True,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "ITEM_PIPELINES": {
            "statskontoret_scraper.crawl.CollectItemsPipeline": 100,
        },
    }
    if IpRotatorMiddleware.is_enabled():
        settings["DOWNLOADER_MIDDLEWARES"] = {
            "statskontoret_scraper.ip_rotator.IpRotatorMiddleware": 800,
        }
        settings["IP_ROTATOR_DOMAINS"] = sorted(
            {
                f"https://{domain}"
                for source in sources
                for domain in source.allowed_domains
            }
        )
    return settings


def _spider_for_source(source: SourceConfig):
    if source.kind == "sitemap":
        return StatskontoretSpider
    if source.kind == "seeded":
        return ForumSpider
    raise ValueError(f"Unsupported source kind: {source.kind}")


def _scope_sources(
    sources: list[SourceConfig], url_prefixes: list[str] | None
) -> list[SourceConfig]:
    if not url_prefixes:
        return sources

    scoped: list[SourceConfig] = []
    unmatched = set(url_prefixes)
    for source in sources:
        matching = tuple(
            prefix
            for prefix in url_prefixes
            if urlsplit(prefix).hostname in source.allowed_domains
        )
        if not matching:
            continue
        unmatched.difference_update(matching)
        scoped.append(
            replace(
                source,
                start_urls=matching,
                include_url_prefixes=matching,
            )
        )

    if unmatched:
        raise ValueError(
            "URL prefixes do not match the selected sources: "
            + ", ".join(sorted(unmatched))
        )
    return scoped


def crawl_sources(
    source_names: list[str] | None = None,
    url_prefixes: list[str] | None = None,
) -> list[RawPage]:
    load_dotenv()
    selected_sources = (
        [get_source(name) for name in source_names] if source_names else load_sources()
    )
    sources = _scope_sources(selected_sources, url_prefixes)

    CollectItemsPipeline.items = []
    process = CrawlerProcess(_settings(sources))
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
