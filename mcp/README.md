---
title: Statskontoret MCP
emoji: 📚
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
short_description: MCP för Statskontorets webbplatser och myndighetsnyckeltal.
datasets:
  - Statskontoretdatalabb/StatskontoretWebsites
  - Statskontoretdatalabb/Myndighetsnyckeltal
tags:
  - mcp
  - swedish
  - public-sector
  - statskontoret
disable_embedding: true
---

This is the code of a lightweight MCP server exposing a full text search API to browse through the content of Statskontoret's websites. It fetches its data from the HuggingFace dataset [Statskontoretdatalabb/StatskontoretWebsites](https://huggingface.co/datasets/Statskontoretdatalabb/StatskontoretWebsites).

This directory is synced to the Hugging Face Space [Statskontoretdatalabb/StatskontoretMCP](https://huggingface.co/spaces/Statskontoretdatalabb/StatskontoretMCP). The space acts as the infrastructure for the server. If you are reading this on HuggingFace, you can access the whole project's repository at [github.com/Statskontoretdatalabb/StatskontoretScraper](https://github.com/Statskontoretdatalabb/StatskontoretScraper).

## Tools

- `health()`
- `kb_info()`
- `search_docs(query, limit=10, source=None)`
- `fetch_doc(page_id)`
- `browse_docs(limit=50, source=None)`
- `list_metrics()`
- `find_agencies(query="", limit=30)`
- `get_indicators(metric, organisation_numbers, denominator="Ingen", start_year=2017, end_year=2025)`
- `show_comparison(...)`: samma årsserier som `get_indicators`, med ett diagram och en tabell i klienter som stöder MCP Apps.

Nyckeltalsverktygen använder [Myndighetsnyckeltal](https://huggingface.co/datasets/Statskontoretdatalabb/Myndighetsnyckeltal),
med en datasetrevision låst i `nyckeltal.py`. Datasetet hämtas först när något av dessa verktyg anropas.
Uppgifternas riktighet garanteras inte, de uppdateras inte automatiskt och kan vara inaktuella eller avvika från Forum.
Saknade observationer returneras som null. Kvoter hämtas direkt från källan utan omräkning.
Alla verktyg finns på samma befintliga `/mcp`-endpoint.


## Local Run

```bash
cd mcp
uv run app.py
```

The server listens on `localhost:7860/mcp`.

MCP-appens källkod finns i `ui/`. Bygg om `comparison.html` med `npm ci` och `node build.mjs` från den katalogen.
