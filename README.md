# Statskontoret Scraper

This repository scrapes the public websites of Statskontoret and publishes their text as structured open data on HuggingFace ([Statskontoretdatalabb/StatskontoretWebsites](https://huggingface.co/datasets/Statskontoretdatalabb/StatskontoretWebsites)) every night.

The `mcp/` directory contains the code for a lightweight MCP server that is hosted on [HuggingFace](https://huggingface.co/spaces/Statskontoretdatalabb/StatskontoretMCP) and exposes the text data to AI clients. To integrate it in your assistant, you can just use the MCP's public endpoint:

```text
https://statskontoretdatalabb-statskontoretmcp.hf.space/mcp
```

## Install

Using `uv`:

```bash
uv sync
```

This installs the lightweight föreskrifter client. Install the optional dataset
dependencies to run the Scrapy crawler, build Parquet files, or publish to
Hugging Face:

```bash
uv sync --extra dataset
```

Install it as a dependency from GitHub in another project:

```bash
uv add "statskontoret-scraper @ git+https://github.com/Statskontoretdatalabb/StatskontoretScraper.git"
```

Fetch the current regulations and general advice from EA-regelverket as Python
dictionaries suitable for a Ferenda source adapter:

```python
from statskontoret_scraper import fetch_foreskrifter

records = fetch_foreskrifter()
```

This lightweight API uses HTTPX and Beautiful Soup. It does not import Scrapy,
PyArrow, Hugging Face, or Markdownify. The records preserve the HTML of
`foreskrift` and `allmanna_rad` sections separately and include Ferenda's
`fs`, `basefile`, `identifier`, `title`, `publisher`, and `url` metadata.

The full dataset crawler remains available after installing the `dataset`
extra:

```python
from statskontoret_scraper import crawl_sources

pages = crawl_sources(["forum"])
```

`crawl_sources()` starts Scrapy's reactor and should only be called once in a
process. Run it in a separate process when integrating it into a long-running
application or when multiple crawls are needed.

AWS API Gateway IP rotation is optional. It is useful in GitHub Actions, where
Statskontoret blocks non-EU traffic. To enable it, install the extra and provide
AWS credentials in `.env` or the environment:

```bash
uv sync --extra dataset --extra ip-rotator
USE_IP_ROTATOR=true
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

The gateway uses the `eu-north-1` region and is removed after the crawl. Leave
`USE_IP_ROTATOR` unset for normal local crawling. For GitHub Actions, add the AWS
values as repository secrets and set the `USE_IP_ROTATOR` repository variable to
`true`.

To publish, create a `.env` file with:

```bash
HF_TOKEN=hf_...
```

## Run

Write the föreskrifter records as JSON:

```bash
uv run statskontoret-scraper foreskrifter
```

Run the full local build:

```bash
uv run statskontoret-scraper build
```

Artifacts are written to `build/latest/`.

Run a single source:

```bash
uv run statskontoret-scraper crawl --source statskontoret
uv run statskontoret-scraper crawl --source forum
```

Publish the generated artifacts to Hugging Face:

```bash
uv run statskontoret-scraper publish
```
