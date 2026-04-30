from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import duckdb
from fastmcp import FastMCP
from huggingface_hub import hf_hub_download
from starlette.responses import HTMLResponse

DATASET_REPO_ID = "Statskontoretdatalabb/StatskontoretWebsites"
PARQUET_FILES = ("statskontoret_pages.parquet", "forum_pages.parquet")
SPACE_README_URL = "https://huggingface.co/spaces/Statskontoretdatalabb/StatskontoretMCP/blob/main/README.md"


@dataclass(frozen=True)
class DatasetInfo:
    generated_at: str | None
    page_count: int
    sources: dict[str, int]


@dataclass(frozen=True)
class StartupStatus:
    started_at: str
    finished_at: str
    startup_seconds: float
    status: str


class KnowledgeBase:
    def __init__(self) -> None:
        self.dataset_repo_id = os.getenv("HF_DATASET_REPO_ID", DATASET_REPO_ID)
        self.conn = duckdb.connect(database=":memory:")
        self.dataset_info = self._load_dataset()

    def _load_dataset(self) -> DatasetInfo:
        parquet_paths = [self._download_file(filename) for filename in PARQUET_FILES]
        build_json = self._download_file("build.json")

        self.conn.execute("INSTALL fts;")
        self.conn.execute("LOAD fts;")
        self.conn.execute(
            """
            CREATE TABLE pages AS
            SELECT * FROM read_parquet($1)
            UNION ALL
            SELECT * FROM read_parquet($2)
            """,
            parquet_paths,
        )
        self.conn.execute(
            """
            PRAGMA create_fts_index(
                'pages',
                'page_id',
                'title',
                'plain_text_content',
                stemmer = 'swedish',
                stopwords = 'none',
                ignore = '(\\.|[^[:alpha:]])+',
                strip_accents = 1,
                lower = 1,
                overwrite = 1
            )
            """
        )

        metadata = json.loads(Path(build_json).read_text(encoding="utf-8"))
        return DatasetInfo(
            generated_at=metadata.get("generated_at"),
            page_count=int(metadata.get("page_count", 0)),
            sources={
                key: int(value) for key, value in metadata.get("sources", {}).items()
            },
        )

    def _download_file(self, filename: str) -> str:
        return hf_hub_download(
            repo_id=self.dataset_repo_id,
            repo_type="dataset",
            filename=filename,
        )

    def kb_info(self) -> dict[str, Any]:
        return {
            "dataset_repo_id": self.dataset_repo_id,
            "generated_at": self.dataset_info.generated_at,
            "page_count": self.dataset_info.page_count,
            "sources": self.dataset_info.sources,
            "index_type": "duckdb_fts",
            "document_granularity": "page",
            "limitations": [
                "Search is lexical BM25 over page-level documents.",
                "The DuckDB FTS index is rebuilt on Space startup.",
            ],
        }

    def browse_docs(
        self, limit: int = 50, source: str | None = None
    ) -> list[dict[str, Any]]:
        query = """
            SELECT page_id, title, source_system, source_url, updated_at
            FROM pages
        """
        params: list[Any] = []
        if source:
            query += " WHERE source_system = ?"
            params.append(source)
        query += " ORDER BY source_system, title LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [
            {
                "page_id": page_id,
                "title": title,
                "source_system": source_system,
                "source_url": source_url,
                "updated_at": updated_at,
            }
            for page_id, title, source_system, source_url, updated_at in rows
        ]

    def fetch_doc(self, page_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT page_id, title, markdown_content, source_system, source_url, updated_at, content_hash
            FROM pages
            WHERE page_id = ?
            """,
            [page_id],
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown page_id: {page_id}")
        return {
            "page_id": row[0],
            "title": row[1],
            "markdown_content": row[2],
            "source_system": row[3],
            "source_url": row[4],
            "updated_at": row[5],
            "content_hash": row[6],
        }

    def search_docs(
        self,
        query: str,
        limit: int = 10,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT
                page_id,
                title,
                source_system,
                source_url,
                updated_at,
                plain_text_content,
                fts_main_pages.match_bm25(page_id, ?, fields := 'title,plain_text_content') AS score
            FROM pages
        """
        params: list[Any] = [query]
        clauses = ["score IS NOT NULL"]
        if source:
            clauses.append("source_system = ?")
            params.append(source)
        sql = (
            f"SELECT * FROM ({sql}) AS ranked "
            f"WHERE {' AND '.join(clauses)} ORDER BY score DESC LIMIT ?"
        )
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [
            {
                "page_id": page_id,
                "title": title,
                "source_system": source_system,
                "source_url": source_url,
                "updated_at": updated_at,
                "score": score,
                "snippet": _make_snippet(plain_text_content, query),
            }
            for page_id, title, source_system, source_url, updated_at, plain_text_content, score in rows
        ]


def _make_snippet(text: str, query: str, window: int = 220) -> str:
    cleaned = " ".join(text.split())
    terms = [re.escape(term) for term in query.split() if term.strip()]
    if not cleaned or not terms:
        return cleaned[:window]
    match = re.search("|".join(terms), cleaned, flags=re.IGNORECASE)
    if match is None:
        return cleaned[:window]
    start = max(match.start() - window // 2, 0)
    end = min(start + window, len(cleaned))
    snippet = cleaned[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(cleaned):
        snippet = snippet + "..."
    return snippet


_startup_started = datetime.now(UTC).isoformat()
_startup_t0 = perf_counter()
kb = KnowledgeBase()
startup_status = StartupStatus(
    started_at=_startup_started,
    finished_at=datetime.now(UTC).isoformat(),
    startup_seconds=round(perf_counter() - _startup_t0, 3),
    status="ready",
)
mcp = FastMCP(
    name="StatskontoretMCP",
    version="0.1.0",
    instructions=(
        "Use this server to search and fetch public page-level content from Statskontoret websites. "
        "Search results are lexical and should usually be followed by fetch_doc for the full markdown."
    ),
)


@mcp.custom_route("/", methods=["GET"])
async def root_page(request) -> HTMLResponse:
    base_url = str(request.base_url).rstrip("/")
    base_url = (
        base_url.replace("http://", "https://")
        if "localhost" not in base_url
        else base_url
    )
    mcp_url = f"{base_url}/mcp"
    html = (
        "<!doctype html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Statskontoret MCP</title>"
        "</head>"
        '<body style="font-family: sans-serif; max-width: 48rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.5;">'
        "<p>This space doesn't have a user interface. It is used to host an MCP server that can be found at: "
        f"<a href='{mcp_url}' target='_blank' rel='noopener noreferrer'>{mcp_url}</a>. "
        f"You can read more <a href='{SPACE_README_URL}' target='_blank' rel='noopener noreferrer'>here</a>.</p>"
        "</body>"
        "</html>"
    )
    return HTMLResponse(html)


@mcp.tool
def kb_info() -> dict[str, Any]:
    """Return metadata about the knowledge base and its current runtime index."""
    return kb.kb_info()


@mcp.tool
def health() -> dict[str, Any]:
    """Return the current runtime status of the server."""
    return {
        "status": startup_status.status,
    }


@mcp.tool
def search_docs(
    query: str, limit: int = 10, source: str | None = None
) -> list[dict[str, Any]]:
    """Search page-level documents by lexical BM25 ranking."""
    return kb.search_docs(query=query, limit=limit, source=source)


@mcp.tool
def fetch_doc(page_id: str) -> dict[str, Any]:
    """Fetch the full markdown content of a page by stable page ID."""
    return kb.fetch_doc(page_id=page_id)


@mcp.tool
def browse_docs(limit: int = 50, source: str | None = None) -> list[dict[str, Any]]:
    """Browse available pages, optionally filtered by source."""
    return kb.browse_docs(limit=limit, source=source)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "7860")),
    )
