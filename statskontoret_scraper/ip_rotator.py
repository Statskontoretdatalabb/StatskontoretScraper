from __future__ import annotations

import os

from scrapy import Request, signals
from scrapy.crawler import Crawler
from scrapy.http import Headers, Response
from scrapy.responsetypes import responsetypes


class _RotatorSession:
    def __init__(self, domains: tuple[str, ...]):
        try:
            import httpx
            from httpx_ip_rotator import AsyncApiGatewayTransport
        except ImportError as exc:
            raise RuntimeError(
                "IP rotation requires the optional dependency: "
                "run `uv sync --extra ip-rotator`."
            ) from exc

        self.transports = {
            domain: AsyncApiGatewayTransport(
                domain,
                regions=["eu-north-1"],
                retries=3,
            )
            for domain in domains
        }
        started = []
        try:
            for transport in self.transports.values():
                transport.start()
                started.append(transport)
        except Exception:
            for transport in started:
                transport.shutdown()
            raise

        self.client = httpx.AsyncClient(mounts=self.transports, timeout=15)

    async def request(self, request: Request) -> Response:
        response = await self.client.request(
            request.method,
            request.url,
            headers=[
                (key, value)
                for key, values in request.headers.items()
                for value in values
            ],
            content=request.body,
        )
        headers = Headers(
            (key, value)
            for key, value in response.headers.multi_items()
            if key.lower() not in {"content-encoding", "content-length"}
        )
        response_type = responsetypes.from_args(
            headers=headers,
            url=request.url,
            body=response.content,
        )
        return response_type(
            url=request.url,
            status=response.status_code,
            headers=headers,
            body=response.content,
            request=request,
        )

    async def close(self) -> None:
        try:
            await self.client.aclose()
        finally:
            first_error = None
            for transport in self.transports.values():
                try:
                    transport.shutdown()
                except Exception as exc:
                    first_error = first_error or exc
            if first_error:
                raise first_error


class IpRotatorMiddleware:
    _session: _RotatorSession | None = None
    _users = 0

    def __init__(self, domains: tuple[str, ...]):
        if self.__class__._session is None:
            self.__class__._session = _RotatorSession(domains)
        self.session = self.__class__._session
        self.__class__._users += 1
        self.closed = False

    @staticmethod
    def is_enabled() -> bool:
        return os.getenv("USE_IP_ROTATOR", "").lower() in {"1", "true", "yes", "on"}

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> IpRotatorMiddleware:
        middleware = cls(tuple(crawler.settings.getlist("IP_ROTATOR_DOMAINS")))
        crawler.signals.connect(middleware.close, signal=signals.engine_stopped)
        return middleware

    async def process_request(self, request: Request) -> Response:
        return await self.session.request(request)

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.__class__._users -= 1
        if self.__class__._users == 0:
            try:
                await self.session.close()
            finally:
                self.__class__._session = None
