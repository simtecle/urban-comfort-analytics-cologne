"""Export Cologne city part geometries for Power BI Shape Map."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "qgis" / "exports" / "cologne_city_parts.geojson"


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
    query = text(
        """
        select jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'properties', jsonb_build_object(
                        'city_part_id', city_part_id,
                        'city_part_name', city_part_name,
                        'borough_name', borough_name,
                        'area_km2', area_km2
                    ),
                    'geometry', st_asgeojson(geometry)::jsonb
                )
                order by city_part_id
            )
        )::text as geojson
        from staging.city_parts
        where geometry is not null
        """
    )

    with engine.connect() as conn:
        geojson_text = conn.execute(query).scalar_one()

    payload = json.loads(geojson_text)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
