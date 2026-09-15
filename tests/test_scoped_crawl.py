from __future__ import annotations

import unittest

from statskontoret_scraper.config import get_source
from statskontoret_scraper.crawl import _scope_sources
from statskontoret_scraper.spiders import ForumSpider


class ScopedCrawlTest(unittest.TestCase):
    def test_limits_start_urls_and_discovered_pages_to_prefix(self) -> None:
        prefix = "https://forum.statskontoret.se/konsekvensutredning/"
        source = _scope_sources([get_source("forum")], [prefix])[0]
        spider = ForumSpider(source)

        self.assertEqual(source.start_urls, (prefix,))
        self.assertFalse(spider.should_skip(f"{prefix}utgangspunkter/"))
        self.assertTrue(spider.should_skip("https://forum.statskontoret.se/styrning/"))

    def test_rejects_prefix_outside_selected_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "do not match"):
            _scope_sources(
                [get_source("forum")],
                ["https://www.statskontoret.se/om-statskontoret/"],
            )

    def test_no_prefix_preserves_source_configuration(self) -> None:
        source = get_source("forum")

        self.assertEqual(_scope_sources([source], None), [source])


if __name__ == "__main__":
    unittest.main()
