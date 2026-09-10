from statskontoret_scraper.config import SourceConfig, get_source, load_sources
from statskontoret_scraper.foreskrifter import fetch_foreskrifter
from statskontoret_scraper.models import RawPage

__all__ = [
    "RawPage",
    "SourceConfig",
    "__version__",
    "crawl_sources",
    "fetch_foreskrifter",
    "get_source",
    "load_sources",
]

__version__ = "0.1.0"


def crawl_sources(source_names: list[str] | None = None) -> list[RawPage]:
    from statskontoret_scraper.crawl import crawl_sources as run_crawl

    return run_crawl(source_names)
