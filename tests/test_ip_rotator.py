from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scrapy import Request
from scrapy.http import HtmlResponse

from statskontoret_scraper.config import SourceConfig
from statskontoret_scraper.crawl import _settings
from statskontoret_scraper.ip_rotator import IpRotatorMiddleware, _RotatorSession


class IpRotatorSettingsTest(unittest.TestCase):
    source = SourceConfig(
        name="example",
        kind="seeded",
        allowed_domains=("www.statskontoret.se", "forum.statskontoret.se"),
        start_urls=(),
        content_selectors=(),
        title_selector="h1",
        updated_meta_names=(),
    )

    def test_ip_rotator_is_disabled_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = _settings([self.source])

        self.assertNotIn("DOWNLOADER_MIDDLEWARES", settings)
        self.assertNotIn("IP_ROTATOR_DOMAINS", settings)

    def test_ip_rotator_configures_all_source_domains(self) -> None:
        with patch.dict(os.environ, {"USE_IP_ROTATOR": "true"}, clear=True):
            settings = _settings([self.source])

        self.assertEqual(
            settings["IP_ROTATOR_DOMAINS"],
            [
                "https://forum.statskontoret.se",
                "https://www.statskontoret.se",
            ],
        )
        self.assertIn(
            "statskontoret_scraper.ip_rotator.IpRotatorMiddleware",
            settings["DOWNLOADER_MIDDLEWARES"],
        )

    def test_false_string_does_not_enable_ip_rotator(self) -> None:
        with patch.dict(os.environ, {"USE_IP_ROTATOR": "false"}, clear=True):
            self.assertFalse(IpRotatorMiddleware.is_enabled())


class RotatorSessionTest(unittest.IsolatedAsyncioTestCase):
    async def test_httpx_response_is_converted_to_scrapy_response(self) -> None:
        class FakeHeaders:
            def multi_items(self):
                return [
                    ("content-type", "text/html; charset=utf-8"),
                    ("content-encoding", "gzip"),
                    ("content-length", "25"),
                ]

        class FakeHttpxResponse:
            url = "https://gateway.execute-api.eu-north-1.amazonaws.com/page"
            status_code = 200
            headers = FakeHeaders()
            content = b"<html><h1>Page</h1></html>"

        class FakeClient:
            async def request(self, method, url, **kwargs):
                self.request_args = (method, url, kwargs)
                return FakeHttpxResponse()

        session = _RotatorSession.__new__(_RotatorSession)
        session.client = FakeClient()
        request = Request("https://www.statskontoret.se/page")

        response = await session.request(request)

        self.assertIsInstance(response, HtmlResponse)
        self.assertEqual(response.request, request)
        self.assertEqual(response.url, request.url)
        self.assertNotIn("Content-Encoding", response.headers)
        self.assertNotIn("Content-Length", response.headers)
        self.assertEqual(response.css("h1::text").get(), "Page")
