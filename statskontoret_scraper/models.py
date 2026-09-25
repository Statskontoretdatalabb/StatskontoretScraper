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
    responsible_agency: str | None = None
    agency_url: str | None = None
    application_period: str | None = None
    requisition_period: str | None = None
    grant_period: str | None = None
    application_status: str | None = None
    area: str | None = None
    eligible_recipients: str | None = None
    application_url: str | None = None
    total_amount: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
