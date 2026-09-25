from __future__ import annotations

import unittest

import scrapy
from scrapy.http import HtmlResponse

from statskontoret_scraper.config import get_source
from statskontoret_scraper.spiders import GRANTS_INDEX_URL, StatskontoretSpider


def response(url: str, html: str) -> HtmlResponse:
    return HtmlResponse(
        url,
        body=html.encode("utf-8"),
        encoding="utf-8",
        headers={"Content-Type": "text/html; charset=utf-8"},
    )


class StatsbidragSpiderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.spider = StatskontoretSpider(get_source("statskontoret"))

    def test_index_follows_grants_and_next_page(self) -> None:
        first = response(
            GRANTS_INDEX_URL,
            """<article><h1>Hitta statsbidrag</h1>
            <ul class="search_results"><li><h2>
              <a href="/statsbidrag/first-grant/550">First grant</a>
            </h2></li></ul>
            <nav class="pagination"><li class="next">
              <button value="2">Nästa</button>
            </li></nav></article>""",
        )

        items = list(self.spider.parse_grants_index(first))

        self.assertEqual(items[0]["title"], "Hitta statsbidrag")
        requests = [item for item in items if isinstance(item, scrapy.Request)]
        self.assertEqual(
            [request.url for request in requests],
            [
                "https://www.statskontoret.se/statsbidrag/first-grant/550",
                f"{GRANTS_INDEX_URL}Sok?P=2",
            ],
        )

        second = response(
            requests[1].url,
            """<ul class="search_results"><li><h2>
            <a href="/statsbidrag/second-grant/549">Second grant</a>
            </h2></li></ul>""",
        )
        later = list(self.spider.parse_grants_index(second))
        self.assertEqual(len(later), 1)
        self.assertEqual(later[0].url, "https://www.statskontoret.se/statsbidrag/second-grant/549")

    def test_grant_detail_preserves_text_and_metadata(self) -> None:
        grant = response(
            "https://www.statskontoret.se/statsbidrag/kalkning/214",
            """<html><head><meta name="last-modified" content="2026-09-02" /></head>
            <body><h1>Kalkning av sjöar</h1><article id="page"><div class="page_body">
            <h1>Kalkning av sjöar</h1>
            <p><strong>Ansvarig myndighet:</strong>
              <a href="https://example.se/bidrag">Havs- och vattenmyndigheten</a></p>
            <div class="statsbidrag-fact-box">
              <div><strong>Ansökningsperiod:</strong><span>2026-01-01 – 2026-12-31</span></div>
              <div><strong>Rekvisitionsperiod:</strong><span>2026-02-01 – 2026-11-30</span></div>
              <div><strong>Bidragsperiod:</strong><span>2026-01-01 – 2026-12-31</span></div>
              <div><strong>Status för ansökan/rekvisition:</strong><span>Öppen</span></div>
              <div><strong>Område:</strong><span>Klimat, miljö och natur</span></div>
              <div><strong>För vilka:</strong><span>Kommuner | Regioner</span></div>
            </div>
            <h2>Syfte med statsbidraget</h2><p>Motverka försurning.</p>
            <h2>Statsbidragets storlek</h2><p>Totalt belopp: 169 000 tkr</p>
            <a class="btn btn-primary" href="https://example.se/ansok">Ansök</a>
            </div></article></body></html>""",
        )

        page = list(self.spider.parse_grant(grant))[0]

        self.assertEqual(page["title"], "Kalkning av sjöar")
        self.assertIn("Motverka försurning.", page["markdown_content"])
        self.assertEqual(page["responsible_agency"], "Havs- och vattenmyndigheten")
        self.assertEqual(page["agency_url"], "https://example.se/bidrag")
        self.assertEqual(page["application_period"], "2026-01-01 – 2026-12-31")
        self.assertEqual(page["requisition_period"], "2026-02-01 – 2026-11-30")
        self.assertEqual(page["grant_period"], "2026-01-01 – 2026-12-31")
        self.assertEqual(page["application_status"], "Öppen")
        self.assertEqual(page["area"], "Klimat, miljö och natur")
        self.assertEqual(page["eligible_recipients"], "Kommuner | Regioner")
        self.assertEqual(page["application_url"], "https://example.se/ansok")
        self.assertEqual(page["total_amount"], "Totalt belopp: 169 000 tkr")

    def test_missing_grant_metadata_is_null(self) -> None:
        grant = response(
            "https://www.statskontoret.se/statsbidrag/other/1",
            "<article id='page'><h1>Other grant</h1><div class='page_body'></div></article>",
        )

        page = list(self.spider.parse_grant(grant))[0]

        self.assertIsNone(page["application_period"])
        self.assertIsNone(page["responsible_agency"])
        self.assertIsNone(page["application_url"])
        self.assertIsNone(page["total_amount"])


if __name__ == "__main__":
    unittest.main()
