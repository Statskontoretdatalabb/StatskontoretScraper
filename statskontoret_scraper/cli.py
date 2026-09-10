from __future__ import annotations

import argparse
import json
from pathlib import Path

from statskontoret_scraper.config import load_sources

DEFAULT_OUTPUT_DIR = Path("build/latest")
DEFAULT_DATASET_REPO_ID = "Statskontoretdatalabb/StatskontoretWebsites"


def crawl_sources(source_names: list[str] | None = None):
    from statskontoret_scraper.crawl import crawl_sources as run_crawl

    return run_crawl(source_names)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="statskontoret-scraper",
        description="Scrape Statskontoret public websites into local dataset artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "foreskrifter",
        help="Write current EA-regelverket regulations as JSON.",
    )

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
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated artifacts.",
    )

    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish an artifact directory to the Hugging Face dataset repo.",
    )
    publish_parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory containing build artifacts.",
    )
    publish_parser.add_argument(
        "--dataset-repo-id",
        default=DEFAULT_DATASET_REPO_ID,
        help="Target Hugging Face dataset repo.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "foreskrifter":
        from statskontoret_scraper.foreskrifter import fetch_foreskrifter

        print(json.dumps(fetch_foreskrifter(), ensure_ascii=False, indent=2))
        return

    if args.command == "crawl":
        pages = crawl_sources(args.source)
        print(f"Crawled {len(pages)} pages")
        return

    if args.command == "build":
        from statskontoret_scraper.artifacts import write_build_artifacts

        pages = crawl_sources(args.source)
        write_build_artifacts(pages, Path(args.output_dir))
        print(f"Wrote build artifacts for {len(pages)} pages to {args.output_dir}")
        return

    if args.command == "publish":
        from statskontoret_scraper.publish import publish_artifacts

        publish_artifacts(
            artifact_dir=Path(args.input_dir),
            dataset_repo_id=args.dataset_repo_id,
        )
        print(f"Published artifacts from {args.input_dir} to {args.dataset_repo_id}")
        return

    raise ValueError(f"Unsupported command: {args.command}")
