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

To publish, create a `.env` file with:

```bash
HF_TOKEN=hf_...
```

## Run

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
