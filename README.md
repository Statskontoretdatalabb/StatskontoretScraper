# Statskontoret Scraper

This repository scrapes the public websites of Statskontoret and publishes their text as structured open data on HuggingFace ([Statskontoretdatalabb/StatskontoretWebsites](https://huggingface.co/datasets/Statskontoretdatalabb/StatskontoretWebsites)) every night.

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
