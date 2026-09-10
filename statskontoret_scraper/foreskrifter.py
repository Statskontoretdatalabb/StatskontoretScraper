from __future__ import annotations

import re
from collections import deque
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup, Tag

EA_ROOT_URL = "https://forum.statskontoret.se/ea-regelverket/"
DESIGNATION_RE = re.compile(r"\b(ESVFA|STKFA)\s+(\d{4}):(\d+)\b")
PUBLISHERS = {
    "esvfa": "Ekonomistyrningsverket",
    "stkfa": "Statskontoret",
}


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _ea_link(current_url: str, href: str) -> str | None:
    parts = urlsplit(urljoin(current_url, href))
    if (
        parts.scheme not in {"http", "https"}
        or parts.netloc != "forum.statskontoret.se"
        or not parts.path.startswith("/ea-regelverket/")
    ):
        return None
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _parse_record(html: str, url: str) -> dict[str, object] | None:
    soup = BeautifulSoup(html, "html.parser")
    box = soup.select_one("div.regelverk-page__box")
    if box is None:
        return None

    designation = None
    title = None
    for heading in box.find_all(["h1", "h2", "h3"]):
        heading_text = _normalize_text(heading.get_text(" ", strip=True))
        match = DESIGNATION_RE.search(heading_text)
        if match:
            designation = match
            title = heading_text
            break
    if designation is None or title is None:
        return None

    sections = []
    for section in box.select("div.foreskrifter, div.allmanna-rad"):
        section_type = (
            "foreskrift" if "foreskrifter" in section.get("class", []) else "allmanna_rad"
        )
        sections.append({"type": section_type, "html": str(section)})
    if not sections:
        return None

    series, year, number = designation.groups()
    fs = series.lower()
    updated = soup.select_one('meta[name="last-modified"]')
    return {
        "fs": fs,
        "basefile": f"{fs}/{year}:{int(number)}",
        "identifier": f"{series} {year}:{int(number)}",
        "title": title,
        "publisher": PUBLISHERS[fs],
        "url": url,
        "updated_at": updated.get("content") if isinstance(updated, Tag) else None,
        "sections": sections,
    }


def fetch_foreskrifter() -> list[dict[str, object]]:
    """Fetch current EA-regelverket regulations as Ferenda-ready source records."""
    records = []
    pending = deque([EA_ROOT_URL])
    seen = set()

    with httpx.Client(
        follow_redirects=True,
        timeout=30,
        headers={"User-Agent": "StatskontoretScraper/0.1"},
    ) as client:
        while pending:
            url = pending.popleft()
            if url in seen:
                continue
            seen.add(url)

            response = client.get(url)
            response.raise_for_status()
            record = _parse_record(response.text, str(response.url))
            if record is not None:
                records.append(record)

            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.select("a[href]"):
                link = _ea_link(str(response.url), anchor["href"])
                if link is not None and link not in seen:
                    pending.append(link)

    return sorted(
        records,
        key=lambda record: (
            str(record["fs"]),
            str(record["basefile"]).split("/", 1)[1].split(":", 1)[0],
            int(str(record["basefile"]).rsplit(":", 1)[1]),
        ),
    )
