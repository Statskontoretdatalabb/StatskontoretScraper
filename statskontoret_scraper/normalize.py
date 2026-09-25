from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import urlsplit

from markdownify import markdownify as to_markdown
from scrapy.http import Response

from statskontoret_scraper.config import SourceConfig
from statskontoret_scraper.models import RawPage

WHITESPACE_RE = re.compile(r"\s+")


def canonical_page_id(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    if not path:
        path = "/"
    return f"{parts.netloc}{path}".replace("/", "__")


def normalize_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", unescape(text)).strip()


def extract_updated_at(response: Response, source: SourceConfig) -> str | None:
    for meta_name in source.updated_meta_names:
        value = response.css(f'meta[name="{meta_name}"]::attr(content)').get()
        if value:
            return normalize_text(value)
    return None


def extract_markdown(response: Response, source: SourceConfig) -> tuple[str, str]:
    html = None
    for selector in source.content_selectors:
        html = response.css(selector).get()
        if html:
            break
    if not html:
        raise ValueError(f"No content node found for {response.url}")

    if (
        source.name == "antikorruption"
        and urlsplit(response.url).path.rstrip("/") == "/antikorruption"
    ):
        hero = response.css("section.hero").get()
        if hero:
            html = hero + html

    markdown = to_markdown(html, heading_style="ATX")
    markdown = normalize_markdown(markdown)
    plain_text = normalize_text(markdown.replace("#", " "))
    return markdown, plain_text


def normalize_markdown(markdown: str) -> str:
    lines = [line.rstrip() for line in markdown.splitlines()]
    compact: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        compact.append(line)
        previous_blank = is_blank
    return "\n".join(compact).strip()


def build_raw_page(response: Response, source: SourceConfig) -> RawPage:
    markdown, plain_text = extract_markdown(response, source)
    title = normalize_text(response.css(source.title_selector).get() or response.url)
    content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return RawPage(
        page_id=canonical_page_id(response.url),
        source_system=source.name,
        source_url=response.url,
        title=title,
        markdown_content=markdown,
        plain_text_content=plain_text,
        updated_at=extract_updated_at(response, source),
        content_hash=content_hash,
    )


def extract_grant_metadata(response: Response) -> dict[str, str | None]:
    labels = {
        "Ansökningsperiod": "application_period",
        "Rekvisitionsperiod": "requisition_period",
        "Bidragsperiod": "grant_period",
        "Status för ansökan/rekvisition": "application_status",
        "Område": "area",
        "För vilka": "eligible_recipients",
    }
    metadata: dict[str, str | None] = {}
    for strong in response.css("article#page .statsbidrag-fact-box strong"):
        label = normalize_text(strong.css("::text").get() or "").rstrip(":")
        field = labels.get(label)
        if field:
            value = strong.xpath("following-sibling::span[1]//text()").getall()
            metadata[field] = normalize_text(" ".join(value)) or None

    link = response.xpath(
        '//article[@id="page"]//p[strong[normalize-space()="Ansvarig myndighet:"]]/a[1]'
    )
    if link:
        metadata["responsible_agency"] = normalize_text(
            " ".join(link.xpath(".//text()").getall())
        ) or None
        agency_href = link.attrib.get("href")
        metadata["agency_url"] = response.urljoin(agency_href) if agency_href else None

    application_href = response.css("article#page a.btn-primary::attr(href)").get()
    metadata["application_url"] = (
        response.urljoin(application_href) if application_href else None
    )
    amount = response.xpath(
        '//article[@id="page"]//h2[normalize-space()="Statsbidragets storlek"]'
        '/following-sibling::p[1]//text()'
    ).getall()
    metadata["total_amount"] = normalize_text(" ".join(amount)) or None
    return metadata
