---
title: Statskontoret MCP
sdk: docker
app_port: 7860
---

# Statskontoret MCP Space

This is the code of a lightweight MCP server exposing a full text search API to browse through the content of Statskontoret's websites. It fetches its data from the HuggingFace dataset [Statskontoretdatalabb/StatskontoretWebsites](https://huggingface.co/datasets/Statskontoretdatalabb/StatskontoretWebsites).

This directory is synced to the Hugging Face Space [Statskontoretdatalabb/StatskontoretMCP](https://huggingface.co/spaces/Statskontoretdatalabb/StatskontoretMCP). The space acts as the infrastructure for the server.

## Tools

- `health()`
- `kb_info()`
- `search_docs(query, limit=10, source=None)`
- `fetch_doc(page_id)`
- `browse_docs(limit=50, source=None)`

## Local Run

```bash
cd mcp
uv run app.py
```

The server listens on `localhost:7860/mcp`.
