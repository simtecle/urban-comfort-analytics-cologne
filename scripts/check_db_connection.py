"""Check the local Supabase/PostgreSQL connection without printing secrets."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SCHEMAS = {"raw", "staging", "mart", "metadata"}


def get_database_url() -> str:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing in .env")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def main() -> None:
    engine = create_engine(get_database_url(), pool_pre_ping=True)

    with engine.connect() as conn:
        identity = conn.execute(
            text("select current_database() as database_name, current_user as user_name")
        ).mappings().one()
        print(f"Connected database: {identity['database_name']}")
        print(f"Connected user: {identity['user_name']}")

        schemas = {
            row[0]
            for row in conn.execute(
                text(
                    """
                    select schema_name
                    from information_schema.schemata
                    where schema_name in ('raw', 'staging', 'mart', 'metadata')
                    """
                )
            )
        }
        missing = REQUIRED_SCHEMAS - schemas
        if missing:
            raise RuntimeError(f"Missing schemas: {', '.join(sorted(missing))}")
        print("Schemas present: metadata, mart, raw, staging")

        postgis_version = conn.execute(text("select postgis_full_version()")).scalar()
        print(f"PostGIS available: {'yes' if postgis_version else 'no'}")

        weights = conn.execute(
            text(
                """
                select dimension_name, weight
                from metadata.score_weights
                where is_active = true
                order by dimension_name
                """
            )
        ).all()
        if len(weights) != 4:
            raise RuntimeError(f"Expected 4 active score weights, found {len(weights)}")
        print("Active score weights:")
        for dimension_name, weight in weights:
            print(f"- {dimension_name}: {weight}")


if __name__ == "__main__":
    main()
