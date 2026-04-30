from __future__ import annotations

import argparse
from pathlib import Path

from statskontoret_scraper.artifacts import write_build_artifacts
from statskontoret_scraper.config import load_sources
from statskontoret_scraper.crawl import crawl_sources, default_output_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="statskontoret-scraper",
        description="Scrape Statskontoret public websites into local dataset artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl", help="Crawl one or more sources.")
    crawl_parser.add_argument(
        "--source",
        action="append",
        choices=[source.name for source in load_sources()],
        help="Limit the crawl to a source. Repeat to include several sources.",
    )

    build_parser = subparsers.add_parser(
        "build",
        help="Crawl sources and write local build artifacts.",
    )
    build_parser.add_argument(
        "--source",
        action="append",
        choices=[source.name for source in load_sources()],
        help="Limit the build to a source. Repeat to include several sources.",
    )
    build_parser.add_argument(
        "--output-dir",
        default=str(default_output_dir()),
        help="Directory for generated artifacts.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "crawl":
        pages = crawl_sources(args.source)
        print(f"Crawled {len(pages)} pages")
        return

    if args.command == "build":
        pages = crawl_sources(args.source)
        write_build_artifacts(pages, Path(args.output_dir))
        print(f"Wrote build artifacts for {len(pages)} pages to {args.output_dir}")
        return

    raise ValueError(f"Unsupported command: {args.command}")
