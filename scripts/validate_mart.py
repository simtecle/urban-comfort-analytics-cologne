"""Validate the first analytics mart."""

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
        counts = conn.execute(
            text(
                """
                select 'mart.dim_city_parts' as table_name, count(*) as row_count from mart.dim_city_parts
                union all
                select 'mart.fact_transport_access', count(*) from mart.fact_transport_access
                union all
                select 'mart.fact_social_infrastructure', count(*) from mart.fact_social_infrastructure
                union all
                select 'mart.fact_cooling_access', count(*) from mart.fact_cooling_access
                union all
                select 'mart.fact_data_quality', count(*) from mart.fact_data_quality
                union all
                select 'mart.fact_urban_comfort_score', count(*) from mart.fact_urban_comfort_score
                order by table_name
                """
            )
        ).mappings().all()
        top_scores = conn.execute(
            text(
                """
                select city_part_name, borough_name, urban_comfort_score, comfort_rank
                from mart.v_powerbi_city_part_overview
                order by comfort_rank
                limit 5
                """
            )
        ).mappings().all()

    print("Mart table counts:")
    for row in counts:
        print(f"- {row['table_name']}: {row['row_count']}")
        if row["row_count"] != EXPECTED_CITY_PARTS:
            raise RuntimeError(f"{row['table_name']} does not contain {EXPECTED_CITY_PARTS} rows")

    print("Top 5 city parts by MVP score:")
    for row in top_scores:
        print(
            f"- #{row['comfort_rank']} {row['city_part_name']} "
            f"({row['borough_name']}): {row['urban_comfort_score']}"
        )


if __name__ == "__main__":
    main()
