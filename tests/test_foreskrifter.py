from __future__ import annotations

import unittest
from unittest.mock import patch

from statskontoret_scraper.cli import build_parser
from statskontoret_scraper.foreskrifter import _parse_record, fetch_foreskrifter


DETAIL_HTML = """
<html>
  <head><meta name="last-modified" content="2026-01-02 09:22:41"></head>
  <body>
    <div class="regelverk-page__box">
      <h1>Anslagsförordningen (2011:223)</h1>
      <h2>Ekonomistyrningsverkets föreskrifter och allmänna råd
          (ESVFA 2022:3) om anslag och inkomsttitlar</h2>
      <div class="foreskrifter"><p><strong>1 §</strong> En föreskrift.</p></div>
      <div class="allmanna-rad"><p>Ett allmänt råd med hänvisning till ESVFA 2022:1.</p></div>
    </div>
  </body>
</html>
"""


class ForeskrifterParseTest(unittest.TestCase):
    def test_parses_ferenda_metadata_and_typed_sections(self) -> None:
        record = _parse_record(
            DETAIL_HTML,
            "https://forum.statskontoret.se/ea-regelverket/anslag/",
        )

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["fs"], "esvfa")
        self.assertEqual(record["basefile"], "esvfa/2022:3")
        self.assertEqual(record["identifier"], "ESVFA 2022:3")
        self.assertEqual(record["publisher"], "Ekonomistyrningsverket")
        self.assertEqual(record["updated_at"], "2026-01-02 09:22:41")
        self.assertEqual(
            [section["type"] for section in record["sections"]],
            ["foreskrift", "allmanna_rad"],
        )

    def test_ignores_pages_without_regulation_sections(self) -> None:
        self.assertIsNone(
            _parse_record(
                '<div class="regelverk-page__box"><h1>Förvaltning</h1></div>',
                "https://forum.statskontoret.se/ea-regelverket/forvaltning/",
            )
        )


class ForeskrifterFetchTest(unittest.TestCase):
    def test_follows_only_ea_links_and_returns_records(self) -> None:
        root = "https://forum.statskontoret.se/ea-regelverket/"
        detail = root + "anslag/"
        pages = {
            root: (
                '<a href="/ea-regelverket/anslag/?version=2">Anslag</a>'
                '<a href="/vanliga-fragor/">Other</a>'
            ),
            detail: DETAIL_HTML,
        }

        class FakeResponse:
            def __init__(self, url: str, text: str):
                self.url = url
                self.text = text

            def raise_for_status(self) -> None:
                pass

        class FakeClient:
            requested = []

            def __init__(self, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url: str) -> FakeResponse:
                self.requested.append(url)
                return FakeResponse(url, pages[url])

        with patch("statskontoret_scraper.foreskrifter.httpx.Client", FakeClient):
            records = fetch_foreskrifter()

        self.assertEqual(FakeClient.requested, [root, detail])
        self.assertEqual([record["identifier"] for record in records], ["ESVFA 2022:3"])


class ForeskrifterCliTest(unittest.TestCase):
    def test_command_is_available_without_dataset_dependencies(self) -> None:
        args = build_parser().parse_args(["foreskrifter"])

        self.assertEqual(args.command, "foreskrifter")
