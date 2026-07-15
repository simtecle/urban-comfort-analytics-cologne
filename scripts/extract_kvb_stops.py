"""Download the KVB stops dataset into data/raw.

The script stores the raw file first. Loading into Supabase happens separately
so source extraction and database writes remain easy to debug.
"""

from __future__ import annotations

from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "kvb_stops"
KVB_STOPS_CSV_URL = "https://data.webservice-kvb.koeln/service/opendata/haltestellen/csv"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / "kvb_stops.csv"

    response = requests.get(
        KVB_STOPS_CSV_URL,
        timeout=60,
        headers={"User-Agent": "urban-comfort-analytics-cologne/0.1"},
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
