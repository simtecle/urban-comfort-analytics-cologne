"""Validate the KVB raw load in Supabase."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]


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
        summary = conn.execute(
            text(
                """
                select
                    count(*) as row_count,
                    min(longitude) as min_longitude,
                    max(longitude) as max_longitude,
                    min(latitude) as min_latitude,
                    max(latitude) as max_latitude
                from raw.kvb_stops
                """
            )
        ).mappings().one()
        latest_run = conn.execute(
            text(
                """
                select run_name, status, rows_loaded
                from metadata.etl_runs
                where run_name = 'load_kvb_stops'
                order by started_at desc
                limit 1
                """
            )
        ).mappings().one()

    print("KVB raw load summary:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("Latest ETL run:")
    for key, value in latest_run.items():
        print(f"- {key}: {value}")

    if summary["row_count"] <= 0:
        raise RuntimeError("raw.kvb_stops is empty")
    if latest_run["status"] != "success":
        raise RuntimeError("Latest KVB ETL run was not successful")


if __name__ == "__main__":
    main()
