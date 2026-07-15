"""Extract tightly scoped MVP features from OpenStreetMap via Overpass.

Run one dataset at a time to keep downloads small and reviewable, for example:

    python scripts/extract_osm_amenities.py --dataset social_amenities
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "osm"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

COLOGNE_AREA_QUERY = 'area["wikidata"="Q365"]["boundary"="administrative"]->.searchArea;'

QUERIES = {
    "social_amenities": f"""
        [out:json][timeout:120];
        {COLOGNE_AREA_QUERY}
        (
          node["amenity"~"^(school|doctors|pharmacy|library)$"](area.searchArea);
          way["amenity"~"^(school|doctors|pharmacy|library)$"](area.searchArea);
          relation["amenity"~"^(school|doctors|pharmacy|library)$"](area.searchArea);
        );
        out center tags;
    """,
    "cooling_green": f"""
        [out:json][timeout:120];
        {COLOGNE_AREA_QUERY}
        (
          node["amenity"~"^(drinking_water|fountain)$"](area.searchArea);
          way["amenity"~"^(drinking_water|fountain)$"](area.searchArea);
          relation["amenity"~"^(drinking_water|fountain)$"](area.searchArea);
          way["leisure"="park"](area.searchArea);
          relation["leisure"="park"](area.searchArea);
        );
        out center tags;
    """,
    "city_parts": """
        [out:json][timeout:120];
        area["wikidata"="Q365"]["boundary"="administrative"]->.searchArea;
        (
          relation["boundary"="administrative"]["admin_level"="10"]["name"](area.searchArea);
        );
        out body geom;
    """,
}


def run_query(name: str, query: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        timeout=180,
        headers={"User-Agent": "urban-comfort-analytics-cologne/0.1"},
    )
    response.raise_for_status()
    payload = response.json()

    output_path = RAW_DIR / f"{name}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a small OSM dataset for the Cologne MVP.")
    parser.add_argument(
        "--dataset",
        choices=sorted(QUERIES),
        required=True,
        help="Dataset to extract. Run one at a time to keep outputs reviewable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = run_query(args.dataset, QUERIES[args.dataset])
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
