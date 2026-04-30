# Statskontoret Scraper

This repository scrapes the public websites of Statskontoret and publishes their text as structured open data on HuggingFace every night.

## Install

Using `uv`:

```bash
uv sync
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
