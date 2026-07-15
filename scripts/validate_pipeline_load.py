"""Validate the current raw/staging data pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CITY_PARTS = 86


def get_engine():
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing in .env")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True)


def print_rows(title: str, rows) -> None:
    print(title)
    for row in rows:
        print("- " + ", ".join(f"{key}: {value}" for key, value in row.items()))


def main() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        city_parts = conn.execute(
            text(
                """
                select
                    count(*) as city_part_count,
                    count(*) filter (where geometry is null) as missing_geometries,
                    count(*) filter (where not geometry_valid) as invalid_geometries
                from staging.city_parts
                """
            )
        ).mappings().one()
        raw_counts = conn.execute(
            text(
                """
                select 'raw.kvb_stops' as table_name, count(*) as row_count from raw.kvb_stops
                union all
                select 'raw.osm_amenities', count(*) from raw.osm_amenities
                union all
                select 'raw.osm_city_parts', count(*) from raw.osm_city_parts
                order by table_name
                """
            )
        ).mappings().all()
        staging_counts = conn.execute(
            text(
                """
                select 'staging.transport_stops' as table_name, count(*) as row_count from staging.transport_stops
                union all
                select 'staging.amenities', count(*) from staging.amenities
                union all
                select 'staging.city_parts', count(*) from staging.city_parts
                order by table_name
                """
            )
        ).mappings().all()
        unmatched = conn.execute(
            text(
                """
                select 'staging.transport_stops' as table_name, count(*) as unmatched_count
                from staging.transport_stops
                where city_part_id is null
                union all
                select 'staging.amenities', count(*)
                from staging.amenities
                where city_part_id is null
                order by table_name
                """
            )
        ).mappings().all()
        amenity_groups = conn.execute(
            text(
                """
                select amenity_group, amenity_type, count(*) as row_count
                from staging.amenities
                group by amenity_group, amenity_type
                order by amenity_group, row_count desc
                """
            )
        ).mappings().all()

    print("City part validation:")
    for key, value in city_parts.items():
        print(f"- {key}: {value}")
    print_rows("Raw table counts:", raw_counts)
    print_rows("Staging table counts:", staging_counts)
    print_rows("Unmatched city part assignments:", unmatched)
    print_rows("Amenity group counts:", amenity_groups)

    if city_parts["city_part_count"] != EXPECTED_CITY_PARTS:
        raise RuntimeError("City part count does not match expected MVP target")
    if city_parts["missing_geometries"] or city_parts["invalid_geometries"]:
        raise RuntimeError("City part geometry validation failed")


if __name__ == "__main__":
    main()
