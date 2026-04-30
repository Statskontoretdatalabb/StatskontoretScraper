from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceConfig:
    name: str
    kind: str
    allowed_domains: tuple[str, ...]
    start_urls: tuple[str, ...]
    content_selectors: tuple[str, ...]
    title_selector: str
    updated_meta_names: tuple[str, ...]
    exclude_url_prefixes: tuple[str, ...] = ()
    link_selectors: tuple[str, ...] = ()


def load_sources(config_path: Path | None = None) -> list[SourceConfig]:
    path = config_path or Path(__file__).resolve().parent.parent / "sources.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    return [
        SourceConfig(
            name=record["name"],
            kind=record["kind"],
            allowed_domains=tuple(record["allowed_domains"]),
            start_urls=tuple(record["start_urls"]),
            content_selectors=tuple(record["content_selectors"]),
            title_selector=record["title_selector"],
            updated_meta_names=tuple(record.get("updated_meta_names", [])),
            exclude_url_prefixes=tuple(record.get("exclude_url_prefixes", [])),
            link_selectors=tuple(record.get("link_selectors", [])),
        )
        for record in records
    ]


def get_source(name: str, config_path: Path | None = None) -> SourceConfig:
    for source in load_sources(config_path):
        if source.name == name:
            return source
    raise KeyError(f"Unknown source: {name}")
