# Working on Statskontoret Scraper

This file describes how agents should contribute to the project. Read
[README.md](./README.md) before changing the scraper or its public API.

## Understand the repository boundaries

- `statskontoret_scraper/` is the main Python package. It provides the
  lightweight föreskrifter client, optional website crawling, artifact creation,
  and dataset publishing.
- `mcp/` is a separate Python project with its own `pyproject.toml` and
  `uv.lock`. Do not update its environment or lockfile when changing only the
  root package.
- The root package uses optional dependencies for crawling, publishing, and IP
  rotation. Install only the capabilities needed for the task.

## Write issues and focused pull requests

- Use `gh` to work with GitHub issues and pull requests.
- For multiline issue or PR Markdown, use `gh --body-file`; do not rely on
  shell-specific quoting.
- Start implementation from a linked issue. If none exists, suggest creating
  one that describes the problem, scope, and acceptance criteria.
- Keep pull requests narrow and link them to their issue with `Closes #...` or a
  specific dependency such as `Blocked by ...`.
- Make atomic commits that each describe one coherent change.

## Use uv for Python work

- Use `uv` for every Python command. Do not invoke `python`, `python3`, `pip`, or
  `pytest` directly.
- Install the root project's complete development environment with:

  ```bash
  uv sync --all-groups --all-extras
  ```

- For a narrower environment, choose the relevant extras documented in the
  README.
- Run the root test suite with:

  ```bash
  uv run --with pytest pytest
  ```

- Work on the MCP project from its own directory:

  ```bash
  cd mcp
  uv sync
  ```

## Preserve behavior with tests

- Add focused tests for new behavior and regressions.
- Run the existing test suite before and after implementation.
- Prefer deterministic parser and spider tests over live crawls. When a live
  crawl is necessary, restrict it to the smallest relevant URL prefix.
- Do not change tests merely to accommodate an implementation without first
  confirming that the expected behavior should change.

## Keep documentation current

- Keep the README aligned with installation extras, public APIs, CLI commands,
  and operational behavior.
- Document the current system rather than maintaining a changelog in the README.
- Update `mcp/README.md` only when the separate MCP project changes.

## Treat publishing as an external operation

- Building local artifacts is safe when it writes only to a temporary or
  documented build directory.
- Publishing to Hugging Face, changing the hosted dataset, restarting the MCP
  Space, or enabling AWS IP rotation changes external state. Do not perform
  those operations unless the user explicitly requests them.
- Never expose tokens, AWS credentials, or other secrets in commands, logs,
  issues, or pull requests.
