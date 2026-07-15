"""Load extracted raw files into Supabase.

The loader keeps the first MVP deliberately small: source snapshots stay under
data/raw, and Supabase receives only normalized rows that are useful for later
city-part joins and aggregation.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from shapely.geometry import LineString, MultiPolygon
from shapely.ops import polygonize, unary_union
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
KVB_REQUIRED_COLUMNS = {
    "Haltestelle",
    "Name",
    "Haltestellenbereich",
    "XKoordinate",
    "YKoordinate",
    "Betriebsbereich",
    "Linien",
}
BOROUGH_BY_REF_PREFIX = {
    "1": "Innenstadt",
    "2": "Rodenkirchen",
    "3": "Lindenthal",
    "4": "Ehrenfeld",
    "5": "Nippes",
    "6": "Chorweiler",
    "7": "Porz",
    "8": "Kalk",
    "9": "Muelheim",
}


def get_engine():
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing in .env")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True)


def load_kvb_stops(engine) -> int:
    csv_path = RAW_DIR / "kvb_stops" / "kvb_stops.csv"
    if not csv_path.exists():
        print("KVB stops file not found; skipping.")
        return 0

    df = pd.read_csv(csv_path, sep=";", encoding="cp1252")
    missing_columns = KVB_REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise RuntimeError(f"KVB CSV missing columns: {', '.join(sorted(missing_columns))}")

    df = df.dropna(subset=["Haltestelle", "XKoordinate", "YKoordinate"]).copy()
    df["XKoordinate"] = pd.to_numeric(df["XKoordinate"], errors="coerce")
    df["YKoordinate"] = pd.to_numeric(df["YKoordinate"], errors="coerce")
    df = df.dropna(subset=["XKoordinate", "YKoordinate"])

    records = []
    for row in df.to_dict(orient="records"):
        source_record_id = str(row["Haltestelle"])
        longitude = float(row["XKoordinate"])
        latitude = float(row["YKoordinate"])
        records.append(
            {
                "source_record_id": source_record_id,
                "stop_name": row.get("Name"),
                "stop_area": str(row.get("Haltestellenbereich")) if pd.notna(row.get("Haltestellenbereich")) else None,
                "line_info": row.get("Linien"),
                "raw_payload": json.dumps(row, ensure_ascii=False, default=str),
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    with engine.begin() as conn:
        conn.execute(text("delete from raw.kvb_stops where source_id = 'kvb_stops'"))
        conn.execute(
            text(
                """
                insert into raw.kvb_stops
                    (source_record_id, stop_name, stop_area, line_info, raw_payload, latitude, longitude, geom)
                values
                    (:source_record_id, :stop_name, :stop_area, :line_info, cast(:raw_payload as jsonb),
                     :latitude, :longitude, st_setsrid(st_makepoint(:longitude, :latitude), 4326))
                """
            ),
            records,
        )
        conn.execute(
            text(
                """
                insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
                values ('load_kvb_stops', 'success', :rows_loaded, :notes)
                """
            ),
            {
                "rows_loaded": len(records),
                "notes": "Loaded KVB stops from semicolon-delimited cp1252 CSV into raw.kvb_stops.",
            },
        )
    return len(records)


def build_staging_transport_stops(engine) -> int:
    with engine.begin() as conn:
        conn.execute(text("delete from staging.transport_stops where source_id = 'kvb_stops'"))
        result = conn.execute(
            text(
                """
                insert into staging.transport_stops
                    (stop_id, stop_name, stop_area, line_info, city_part_id, geom, source_id)
                select
                    k.source_record_id,
                    k.stop_name,
                    k.stop_area,
                    k.line_info,
                    city_part.city_part_id,
                    k.geom,
                    k.source_id
                from raw.kvb_stops k
                left join lateral (
                    select c.city_part_id
                    from staging.city_parts c
                    where st_covers(c.geometry, k.geom)
                    order by c.city_part_id
                    limit 1
                ) city_part on true
                where k.source_id = 'kvb_stops'
                """
            )
        )
        conn.execute(
            text(
                """
                insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
                values ('build_staging_transport_stops', 'success', :rows_loaded, :notes)
                """
            ),
            {
                "rows_loaded": result.rowcount,
                "notes": "Assigned KVB stops to Cologne city parts using ST_Covers.",
            },
        )
    return int(result.rowcount or 0)


def load_osm_metadata(engine) -> int:
    osm_dir = RAW_DIR / "osm"
    if not osm_dir.exists():
        print("OSM raw directory not found; skipping.")
        return 0

    total_elements = 0
    for json_path in osm_dir.glob("*.json"):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        element_count = len(payload.get("elements", []))
        total_elements += element_count
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
                    values (:run_name, 'raw_file_detected', :rows_loaded, :notes)
                    """
                ),
                {
                    "run_name": f"load_{json_path.stem}",
                    "rows_loaded": element_count,
                    "notes": f"Raw OSM JSON detected at {json_path.name}. Geometry-specific load mapping follows validation.",
                },
            )
    return total_elements


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def relation_to_multipolygon(element: dict) -> MultiPolygon:
    lines = []
    for member in element.get("members", []):
        if member.get("type") != "way" or member.get("role") != "outer":
            continue
        coords = [(point["lon"], point["lat"]) for point in member.get("geometry", [])]
        if len(coords) >= 2:
            lines.append(LineString(coords))

    if not lines:
        raise ValueError(f"Relation {element.get('id')} has no outer geometry ways")

    polygons = [polygon for polygon in polygonize(unary_union(lines)) if not polygon.is_empty]
    if not polygons:
        raise ValueError(f"Relation {element.get('id')} could not be polygonized")

    return MultiPolygon(polygons)


def load_osm_city_parts(engine) -> int:
    json_path = RAW_DIR / "osm" / "city_parts.json"
    if not json_path.exists():
        print("OSM city parts file not found; skipping.")
        return 0

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    records = []
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        multipolygon = relation_to_multipolygon(element)
        ref = tags.get("ref")
        city_part_id = ref if ref else slugify(name)
        borough_name = BOROUGH_BY_REF_PREFIX.get(str(ref)[0]) if ref else None
        records.append(
            {
                "osm_type": element.get("type"),
                "osm_id": int(element["id"]),
                "city_part_id": city_part_id,
                "city_part_name": name,
                "borough_name": borough_name,
                "admin_level": tags.get("admin_level"),
                "raw_tags": json.dumps(tags, ensure_ascii=False),
                "wkt": multipolygon.wkt,
            }
        )

    if not records:
        raise RuntimeError("No OSM city part records parsed")

    with engine.begin() as conn:
        conn.execute(text("delete from staging.city_parts where source_id = 'cologne_city_parts_osm'"))
        conn.execute(text("delete from raw.osm_city_parts where source_id = 'cologne_city_parts_osm'"))
        conn.execute(
            text(
                """
                insert into raw.osm_city_parts
                    (osm_type, osm_id, city_part_name, admin_level, raw_tags, geometry)
                values
                    (:osm_type, :osm_id, :city_part_name, :admin_level, cast(:raw_tags as jsonb),
                     st_multi(st_collectionextract(st_makevalid(st_geomfromtext(:wkt, 4326)), 3)))
                """
            ),
            records,
        )
        conn.execute(
            text(
                """
                insert into staging.city_parts
                    (city_part_id, city_part_name, borough_name, osm_type, osm_id, area_km2,
                     geometry, geometry_valid, source_id)
                select
                    :city_part_id,
                    :city_part_name,
                    :borough_name,
                    :osm_type,
                    :osm_id,
                    round((st_area(st_multi(st_collectionextract(st_makevalid(st_geomfromtext(:wkt, 4326)), 3))::geography) / 1000000)::numeric, 4),
                    st_multi(st_collectionextract(st_makevalid(st_geomfromtext(:wkt, 4326)), 3)),
                    st_isvalid(st_multi(st_collectionextract(st_makevalid(st_geomfromtext(:wkt, 4326)), 3))),
                    'cologne_city_parts_osm'
                """
            ),
            records,
        )
        conn.execute(
            text(
                """
                insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
                values ('load_osm_city_parts', 'success', :rows_loaded, :notes)
                """
            ),
            {
                "rows_loaded": len(records),
                "notes": "Loaded OSM admin_level=10 Cologne city part boundaries into raw and staging tables.",
            },
        )

    return len(records)


def element_coordinates(element: dict) -> tuple[float, float] | None:
    if "lon" in element and "lat" in element:
        return float(element["lon"]), float(element["lat"])
    center = element.get("center")
    if center and "lon" in center and "lat" in center:
        return float(center["lon"]), float(center["lat"])
    return None


def osm_feature_type(tags: dict) -> str | None:
    for key in ("amenity", "leisure", "landuse", "natural"):
        if tags.get(key):
            return str(tags[key])
    return None


def load_osm_amenity_dataset(engine, dataset_name: str, amenity_group: str, source_id: str) -> int:
    json_path = RAW_DIR / "osm" / f"{dataset_name}.json"
    if not json_path.exists():
        print(f"OSM {dataset_name} file not found; skipping.")
        return 0

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    records = []
    for element in payload.get("elements", []):
        coordinates = element_coordinates(element)
        if not coordinates:
            continue
        longitude, latitude = coordinates
        tags = element.get("tags", {})
        records.append(
            {
                "osm_type": element.get("type"),
                "osm_id": int(element["id"]),
                "amenity_group": amenity_group,
                "amenity_type": osm_feature_type(tags),
                "amenity_name": tags.get("name"),
                "raw_tags": json.dumps(tags, ensure_ascii=False),
                "latitude": latitude,
                "longitude": longitude,
                "source_id": source_id,
            }
        )

    if not records:
        print(f"No point-like OSM records parsed for {dataset_name}; skipping.")
        return 0

    with engine.begin() as conn:
        conn.execute(text("delete from raw.osm_amenities where source_id = :source_id"), {"source_id": source_id})
        conn.execute(
            text(
                """
                insert into raw.osm_amenities
                    (osm_type, osm_id, amenity_group, amenity_type, amenity_name, raw_tags,
                     latitude, longitude, geom, source_id)
                values
                    (:osm_type, :osm_id, :amenity_group, :amenity_type, :amenity_name,
                     cast(:raw_tags as jsonb), :latitude, :longitude,
                     st_setsrid(st_makepoint(:longitude, :latitude), 4326), :source_id)
                """
            ),
            records,
        )
        conn.execute(
            text(
                """
                insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
                values (:run_name, 'success', :rows_loaded, :notes)
                """
            ),
            {
                "run_name": f"load_{dataset_name}",
                "rows_loaded": len(records),
                "notes": f"Loaded {dataset_name} OSM point/center features into raw.osm_amenities.",
            },
        )

    return len(records)


def build_staging_amenities(engine) -> int:
    with engine.begin() as conn:
        conn.execute(text("delete from staging.amenities where source_id like 'osm_%'"))
        result = conn.execute(
            text(
                """
                insert into staging.amenities
                    (amenity_id, amenity_group, amenity_type, amenity_name, city_part_id, geom, source_id)
                select
                    concat(a.osm_type, ':', a.osm_id, ':', a.amenity_group) as amenity_id,
                    a.amenity_group,
                    a.amenity_type,
                    a.amenity_name,
                    city_part.city_part_id,
                    a.geom,
                    a.source_id
                from raw.osm_amenities a
                left join lateral (
                    select c.city_part_id
                    from staging.city_parts c
                    where st_covers(c.geometry, a.geom)
                    order by c.city_part_id
                    limit 1
                ) city_part on true
                where a.source_id like 'osm_%'
                """
            )
        )
        conn.execute(
            text(
                """
                insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
                values ('build_staging_amenities', 'success', :rows_loaded, :notes)
                """
            ),
            {
                "rows_loaded": result.rowcount,
                "notes": "Assigned OSM amenities and cooling features to Cologne city parts using ST_Covers.",
            },
        )
    return int(result.rowcount or 0)


def main() -> None:
    engine = get_engine()
    kvb_rows = load_kvb_stops(engine)
    city_parts = load_osm_city_parts(engine)
    staged_stops = build_staging_transport_stops(engine)
    social_amenities = load_osm_amenity_dataset(
        engine,
        dataset_name="social_amenities",
        amenity_group="social_infrastructure",
        source_id="osm_social_amenities",
    )
    cooling_green = load_osm_amenity_dataset(
        engine,
        dataset_name="cooling_green",
        amenity_group="cooling_green",
        source_id="osm_cooling_green",
    )
    staged_amenities = build_staging_amenities(engine)
    osm_elements = load_osm_metadata(engine)
    print(
        "Loaded "
        f"{kvb_rows} KVB rows, {city_parts} city parts, "
        f"{social_amenities} social amenities, {cooling_green} cooling/green features. "
        f"Built {staged_stops} staged stops and {staged_amenities} staged amenities. "
        f"Detected {osm_elements} OSM elements."
    )


if __name__ == "__main__":
    main()
