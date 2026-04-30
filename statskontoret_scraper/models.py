from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RawPage:
    page_id: str
    source_system: str
    source_url: str
    title: str
    markdown_content: str
    plain_text_content: str
    updated_at: str | None
    content_hash: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
