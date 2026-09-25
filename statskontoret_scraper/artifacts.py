from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from statskontoret_scraper.models import RawPage


def write_build_artifacts(pages: list[RawPage], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    pages_by_file: dict[str, list[dict[str, str | None]]] = {}
    source_counts: dict[str, int] = {}
    for page in pages:
        source_counts[page.source_system] = source_counts.get(page.source_system, 0) + 1
        file_source = (
            "statskontoret" if page.source_system == "antikorruption" else page.source_system
        )
        pages_by_file.setdefault(file_source, []).append(page.to_dict())

    for source_name, source_pages in sorted(pages_by_file.items()):
        pq.write_table(
            pa.Table.from_pylist(source_pages),
            output_dir / f"{source_name}_pages.parquet",
        )

    build_metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "page_count": len(pages),
        "sources": dict(sorted(source_counts.items())),
    }
    (output_dir / "build.json").write_text(
        json.dumps(build_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
