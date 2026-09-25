from __future__ import annotations

import json

import pyarrow.parquet as pq

from statskontoret_scraper.artifacts import write_build_artifacts
from statskontoret_scraper.models import RawPage


def test_antikorruption_pages_share_statskontoret_artifact(tmp_path) -> None:
    def page(source: str, **metadata: str) -> RawPage:
        return RawPage(
            page_id=source,
            source_system=source,
            source_url=f"https://example.se/{source}/",
            title=source,
            markdown_content=source,
            plain_text_content=source,
            updated_at=None,
            content_hash=source,
            **metadata,
        )

    write_build_artifacts(
        [
            page("statskontoret", responsible_agency="Grant agency"),
            page("antikorruption"),
            page("forum"),
        ],
        tmp_path,
    )

    assert sorted(path.name for path in tmp_path.glob("*.parquet")) == [
        "forum_pages.parquet",
        "statskontoret_pages.parquet",
    ]
    rows = pq.read_table(tmp_path / "statskontoret_pages.parquet").to_pylist()
    assert [row["source_system"] for row in rows] == [
        "statskontoret",
        "antikorruption",
    ]
    assert rows[0]["responsible_agency"] == "Grant agency"
    assert pq.read_table(tmp_path / "forum_pages.parquet").num_rows == 1
    assert json.loads((tmp_path / "build.json").read_text())["sources"] == {
        "antikorruption": 1,
        "forum": 1,
        "statskontoret": 1,
    }
