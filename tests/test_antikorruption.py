from __future__ import annotations

import unittest

from scrapy.http import TextResponse

from statskontoret_scraper.config import get_source
from statskontoret_scraper.crawl import _scope_sources
from statskontoret_scraper.spiders import StatskontoretSpider


class AntikorruptionTest(unittest.TestCase):
    def test_sitemap_scopes_antikorruption_without_duplicating_main_source(self) -> None:
        source = get_source("antikorruption")
        spider = StatskontoretSpider(source)
        main_spider = StatskontoretSpider(get_source("statskontoret"))
        home = "https://www.statskontoret.se/antikorruption/"
        article = home + "utgangspunkter/korruption/"
        entries = [
            {"loc": home},
            {"loc": article},
            {"loc": home + "sok/"},
            {"loc": "https://www.statskontoret.se/om-statskontoret/"},
        ]

        self.assertEqual(
            list(spider.sitemap_filter(entries)),
            entries[:2],
        )
        self.assertTrue(main_spider.should_skip(home))
        self.assertTrue(main_spider.should_skip(article))

    def test_landing_page_uses_main_content(self) -> None:
        source = get_source("antikorruption")
        spider = StatskontoretSpider(source)
        response = TextResponse(
            url="https://www.statskontoret.se/antikorruption/utgangspunkter/",
            body=b"<html><h1>Gemensamma utgangspunkter</h1><nav>Menu</nav>"
            b"<main id='content'><p>Knowledge and guidance</p></main></html>",
            headers={"Content-Type": "text/html"},
        )

        page = spider.parse_page(response)

        self.assertIsNotNone(page)
        self.assertEqual(page["source_system"], "antikorruption")
        self.assertIn("Knowledge and guidance", page["markdown_content"])
        self.assertNotIn("Menu", page["markdown_content"])

    def test_homepage_includes_intro_and_main_content(self) -> None:
        spider = StatskontoretSpider(get_source("antikorruption"))
        response = TextResponse(
            url="https://www.statskontoret.se/antikorruption/",
            body=b"<html><nav>Menu</nav><section class='hero'><h1>Against corruption</h1>"
            b"<p>Homepage introduction</p></section><main id='content'>"
            b"<p>Guidance cards</p></main></html>",
            headers={"Content-Type": "text/html"},
        )

        page = spider.parse_page(response)

        self.assertIsNotNone(page)
        self.assertIn("Homepage introduction", page["markdown_content"])
        self.assertIn("Guidance cards", page["markdown_content"])
        self.assertNotIn("Menu", page["markdown_content"])

    def test_article_content_takes_priority_over_main_navigation(self) -> None:
        spider = StatskontoretSpider(get_source("antikorruption"))
        response = TextResponse(
            url="https://www.statskontoret.se/antikorruption/utgangspunkter/korruption/",
            body=b"<html><h1>Corruption</h1><main id='content'><nav>Submenu</nav>"
            b"<article><p>Article text</p></article></main></html>",
            headers={"Content-Type": "text/html"},
        )

        page = spider.parse_page(response)

        self.assertIsNotNone(page)
        self.assertIn("Article text", page["markdown_content"])
        self.assertNotIn("Submenu", page["markdown_content"])

    def test_scoped_sitemap_keeps_sitemap_start_url(self) -> None:
        source = get_source("antikorruption")
        prefix = "https://www.statskontoret.se/antikorruption/utgangspunkter/"

        scoped = _scope_sources([source], [prefix])[0]

        self.assertEqual(scoped.start_urls, source.start_urls)
        self.assertEqual(scoped.include_url_prefixes, (prefix,))


if __name__ == "__main__":
    unittest.main()
