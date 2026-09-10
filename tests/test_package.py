from __future__ import annotations

import unittest

import statskontoret_scraper


class PackageTest(unittest.TestCase):
    def test_public_api_is_exported(self) -> None:
        self.assertTrue(callable(statskontoret_scraper.crawl_sources))
        self.assertTrue(callable(statskontoret_scraper.fetch_foreskrifter))
        self.assertTrue(callable(statskontoret_scraper.load_sources))

    def test_bundled_sources_are_loadable(self) -> None:
        sources = statskontoret_scraper.load_sources()

        self.assertEqual(
            [source.name for source in sources],
            ["statskontoret", "forum"],
        )
