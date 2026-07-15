"""Validate the Power BI city part GeoJSON export."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEOJSON_PATH = ROOT / "qgis" / "exports" / "cologne_city_parts.geojson"
EXPECTED_FEATURES = 86


def main() -> None:
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"Missing GeoJSON export: {GEOJSON_PATH}")

    payload = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise RuntimeError("GeoJSON root must be a FeatureCollection")

    features = payload.get("features", [])
    city_part_ids = [feature.get("properties", {}).get("city_part_id") for feature in features]
    missing_ids = [idx for idx, value in enumerate(city_part_ids) if not value]
    duplicate_ids = sorted({value for value in city_part_ids if city_part_ids.count(value) > 1})
    geometry_types = sorted({feature.get("geometry", {}).get("type") for feature in features})

    print(f"GeoJSON features: {len(features)}")
    print(f"Geometry types: {', '.join(geometry_types)}")
    print(f"Missing city_part_id values: {len(missing_ids)}")
    print(f"Duplicate city_part_id values: {len(duplicate_ids)}")

    if len(features) != EXPECTED_FEATURES:
        raise RuntimeError(f"Expected {EXPECTED_FEATURES} features, found {len(features)}")
    if missing_ids:
        raise RuntimeError("Some features are missing city_part_id")
    if duplicate_ids:
        raise RuntimeError(f"Duplicate city_part_id values: {', '.join(duplicate_ids)}")
    if not set(geometry_types).issubset({"Polygon", "MultiPolygon"}):
        raise RuntimeError("Unexpected GeoJSON geometry type found")


if __name__ == "__main__":
    main()
