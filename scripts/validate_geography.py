"""Validate the first geography setup in Supabase."""

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


def main() -> None:
    engine = get_engine()
    with engine.connect() as conn:
        city_part_count = conn.execute(text("select count(*) from staging.city_parts")).scalar()
        missing_geometry_count = conn.execute(
            text("select count(*) from staging.city_parts where geometry is null")
        ).scalar()
        invalid_geometry_count = conn.execute(
            text(
                """
                select count(*)
                from staging.city_parts
                where geometry is not null and not st_isvalid(geometry)
                """
            )
        ).scalar()

    print(f"City parts: {city_part_count} / expected {EXPECTED_CITY_PARTS}")
    print(f"Missing geometries: {missing_geometry_count}")
    print(f"Invalid geometries: {invalid_geometry_count}")

    if city_part_count != EXPECTED_CITY_PARTS:
        raise RuntimeError("City part count does not match expected MVP target.")
    if missing_geometry_count:
        raise RuntimeError("Some city parts are missing geometries.")
    if invalid_geometry_count:
        raise RuntimeError("Some city part geometries are invalid.")


if __name__ == "__main__":
    main()
