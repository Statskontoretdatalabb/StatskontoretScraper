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
