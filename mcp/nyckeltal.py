"""Read the versioned Hub dataset and select values without recomputing source ratios."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import duckdb
from huggingface_hub import hf_hub_download

CONFIG = {
    "repo_id": "Statskontoretdatalabb/Myndighetsnyckeltal",
    "revision": "ec6a12a1c698ba173b33eb4fdc10d01fc5fb17f0",
}
DENOMINATORS = {
    "Ingen": "värde",
    "Antal anställda": "värdeDelatMedAntalAnställda",
    "Antal årsarbetskrafter": "värdeDelatMedÅrsarbetskrafter",
    "Summa verksamhetens kostnader": "värdeDelatMedSummaKostnader",
    "Lokalarea (kvadratmeter)": "värdeDelatMedLokalyta",
}


@lru_cache(maxsize=1)
def load_records() -> list[dict[str, Any]]:
    path = hf_hub_download(
        CONFIG["repo_id"],
        "data/nyckeltal.parquet",
        repo_type="dataset",
        revision=CONFIG["revision"],
    )
    with duckdb.connect(database=":memory:") as connection:
        result = connection.execute("SELECT * FROM read_parquet(?)", [path])
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]


def list_metrics() -> dict[str, Any]:
    """Lista tillgängliga mått, nämnare, år och uppgifternas proveniens."""
    records = load_records()
    return {
        "metrics": sorted({r["typ"] for r in records}),
        "denominators": list(DENOMINATORS),
        "years": sorted({r["år"] for r in records}),
        "agencies": len({r["organisationsnr"] for r in records}),
        "observations": len(records),
        "dataset": CONFIG,
        "source_environment": "test",
        "note": "Ögonblicksbild från källans test-API. Enhet, prisbas och källans uppdateringstid specificeras inte i exporten.",
    }


def find_agencies(query: str = "", limit: int = 30) -> list[dict[str, str]]:
    """Sök myndigheter efter namn eller organisationsnummer.

    Args:
        query: Del av ett myndighetsnamn eller organisationsnummer. Tom sträng listar myndigheter.
        limit: Högsta antal träffar, mellan 1 och 223.
    """
    if not 1 <= limit <= 223:
        raise ValueError("limit måste vara mellan 1 och 223.")
    agencies = {
        r["organisationsnr"]: {
            key: r[key]
            for key in (
                "organisationsnr",
                "myndighet",
                "cofogtypNomenklatur",
                "cofogtypNamn",
            )
        }
        for r in load_records()
    }
    query = query.strip().casefold()
    return [
        r
        for r in sorted(agencies.values(), key=lambda r: r["myndighet"].casefold())
        if query in r["myndighet"].casefold() or query in r["organisationsnr"]
    ][:limit]


def get_indicators(
    metric: str,
    organisation_numbers: list[str],
    denominator: str = "Ingen",
    start_year: int = 2017,
    end_year: int = 2025,
) -> dict[str, Any]:
    """Hämta årsserier för ett mått och upp till tio myndigheter. Saknade värden är null, aldrig noll.

    Args:
        metric: Exakt måttnamn från list_metrics.
        organisation_numbers: En till tio organisationsnummer som text; använd find_agencies för att hitta dem.
        denominator: Ingen eller ett nämnarnamn från list_metrics. Källans färdigberäknade kvot används.
        start_year: Första år i intervallet, 2017–2025.
        end_year: Sista år i intervallet, 2017–2025.
    """
    records = load_records()
    if metric not in {r["typ"] for r in records}:
        raise ValueError(
            "Okänt mått. Använd list_metrics för att se tillgängliga mått."
        )
    if denominator not in DENOMINATORS:
        raise ValueError(
            "Okänd nämnare. Använd list_metrics för att se tillgängliga nämnare."
        )
    if not 2017 <= start_year <= end_year <= 2025:
        raise ValueError(
            "Årsintervallet måste ligga mellan 2017 och 2025, i stigande ordning."
        )
    orgs = list(dict.fromkeys(organisation_numbers))
    if not 1 <= len(orgs) <= 10:
        raise ValueError("Välj mellan en och tio myndigheter.")
    names = {r["organisationsnr"]: r["myndighet"] for r in records}
    if any(org not in names for org in orgs):
        raise ValueError(
            "Okänt organisationsnummer. Använd find_agencies för att hitta myndigheter."
        )
    values = {
        (r["organisationsnr"], r["år"]): r[DENOMINATORS[denominator]]
        for r in records
        if r["typ"] == metric and r["organisationsnr"] in orgs
    }
    years = list(range(start_year, end_year + 1))
    return {
        "metric": metric,
        "denominator": denominator,
        "value_field": DENOMINATORS[denominator],
        "years": years,
        "series": [
            {
                "organisationsnr": org,
                "myndighet": names[org],
                "values": [values.get((org, year)) for year in years],
            }
            for org in orgs
        ],
        "dataset": CONFIG,
        "source_environment": "test",
        "note": "Null anger saknat värde. Ingen skalning, procentomräkning eller inflationsjustering har gjorts. Exporten saknar uttrycklig enhetsinformation.",
    }


UI_URI = "ui://myndighetsnyckeltal/comparison.html"


def comparison_app() -> str:
    """Diagram och tabell för myndighetsnyckeltal, direkt i chatten."""
    return Path(__file__).with_name("comparison.html").read_text()


def register_tools(server) -> None:
    """Add read-only indicator tools to the existing MCP endpoint."""
    for function in (list_metrics, find_agencies, get_indicators):
        server.tool(function, annotations={"readOnlyHint": True})
    server.tool(
        get_indicators,
        name="show_comparison",
        description="Visa myndighetsnyckeltal som ett interaktivt diagram och en tabell i chatten. Samma parametrar och data som get_indicators.",
        annotations={"readOnlyHint": True},
        meta={"ui": {"resourceUri": UI_URI}, "ui/resourceUri": UI_URI},
    )
    server.resource(UI_URI, mime_type="text/html;profile=mcp-app")(comparison_app)
