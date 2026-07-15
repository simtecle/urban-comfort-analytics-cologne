"""Build the first analytics mart and Urban Comfort Score."""

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


def apply_sql_files(engine) -> None:
    for relative_path in ["sql/04_mart_tables.sql", "sql/05_powerbi_views.sql"]:
        sql = (ROOT / relative_path).read_text(encoding="utf-8")
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)


def build_mart(engine) -> None:
    statements = [
        """
        truncate table
            mart.fact_urban_comfort_score,
            mart.fact_data_quality,
            mart.fact_cooling_access,
            mart.fact_social_infrastructure,
            mart.fact_transport_access,
            mart.dim_city_parts
        restart identity
        """,
        """
        insert into mart.dim_city_parts
            (city_part_id, city_part_name, borough_name, area_km2, geometry_available, source_id)
        select
            city_part_id,
            city_part_name,
            borough_name,
            area_km2,
            geometry is not null,
            source_id
        from staging.city_parts
        """,
        """
        insert into mart.fact_transport_access
            (city_part_id, stop_count, stops_per_km2, rail_stop_count, bus_stop_count, unmatched_source_count)
        select
            d.city_part_id,
            count(s.stop_id)::integer as stop_count,
            round((count(s.stop_id)::numeric / nullif(d.area_km2, 0)), 4) as stops_per_km2,
            count(*) filter (where r.raw_payload ->> 'Betriebsbereich' = 'STRAB')::integer as rail_stop_count,
            count(*) filter (where r.raw_payload ->> 'Betriebsbereich' = 'BUS')::integer as bus_stop_count,
            (
                select count(*)::integer
                from staging.transport_stops all_stops
                where all_stops.city_part_id is null
            ) as unmatched_source_count
        from mart.dim_city_parts d
        left join staging.transport_stops s on d.city_part_id = s.city_part_id
        left join raw.kvb_stops r on s.stop_id = r.source_record_id
        group by d.city_part_id, d.area_km2
        """,
        """
        insert into mart.fact_social_infrastructure
            (city_part_id, schools_count, doctors_count, pharmacies_count, libraries_count,
             total_social_amenities, social_amenities_per_km2)
        select
            d.city_part_id,
            count(*) filter (where a.amenity_type = 'school')::integer,
            count(*) filter (where a.amenity_type = 'doctors')::integer,
            count(*) filter (where a.amenity_type = 'pharmacy')::integer,
            count(*) filter (where a.amenity_type = 'library')::integer,
            count(a.amenity_id)::integer,
            round((count(a.amenity_id)::numeric / nullif(d.area_km2, 0)), 4)
        from mart.dim_city_parts d
        left join staging.amenities a
            on d.city_part_id = a.city_part_id
            and a.amenity_group = 'social_infrastructure'
        group by d.city_part_id, d.area_km2
        """,
        """
        insert into mart.fact_cooling_access
            (city_part_id, drinking_water_count, fountain_count, park_count,
             cooling_features_count, cooling_features_per_km2)
        select
            d.city_part_id,
            count(*) filter (where a.amenity_type = 'drinking_water')::integer,
            count(*) filter (where a.amenity_type = 'fountain')::integer,
            count(*) filter (where a.amenity_type = 'park')::integer,
            count(a.amenity_id)::integer,
            round((count(a.amenity_id)::numeric / nullif(d.area_km2, 0)), 4)
        from mart.dim_city_parts d
        left join staging.amenities a
            on d.city_part_id = a.city_part_id
            and a.amenity_group = 'cooling_green'
        group by d.city_part_id, d.area_km2
        """,
        """
        update mart.fact_transport_access t
        set transport_score = scores.score
        from (
            select
                city_part_id,
                case
                    when max(stops_per_km2) over () = min(stops_per_km2) over () then 100
                    else round(
                        100 * (stops_per_km2 - min(stops_per_km2) over ())
                        / nullif(max(stops_per_km2) over () - min(stops_per_km2) over (), 0),
                        2
                    )
                end as score
            from mart.fact_transport_access
        ) scores
        where t.city_part_id = scores.city_part_id
        """,
        """
        update mart.fact_social_infrastructure s
        set social_infrastructure_score = scores.score
        from (
            select
                city_part_id,
                case
                    when max(social_amenities_per_km2) over () = min(social_amenities_per_km2) over () then 100
                    else round(
                        100 * (social_amenities_per_km2 - min(social_amenities_per_km2) over ())
                        / nullif(max(social_amenities_per_km2) over () - min(social_amenities_per_km2) over (), 0),
                        2
                    )
                end as score
            from mart.fact_social_infrastructure
        ) scores
        where s.city_part_id = scores.city_part_id
        """,
        """
        update mart.fact_cooling_access c
        set cooling_score = scores.score
        from (
            select
                city_part_id,
                case
                    when max(cooling_features_per_km2) over () = min(cooling_features_per_km2) over () then 100
                    else round(
                        100 * (cooling_features_per_km2 - min(cooling_features_per_km2) over ())
                        / nullif(max(cooling_features_per_km2) over () - min(cooling_features_per_km2) over (), 0),
                        2
                    )
                end as score
            from mart.fact_cooling_access
        ) scores
        where c.city_part_id = scores.city_part_id
        """,
        """
        insert into mart.fact_data_quality
            (city_part_id, required_indicators_available, required_indicators_total,
             missing_indicator_count, data_quality_score, notes)
        select
            d.city_part_id,
            (
                (case when t.stop_count > 0 then 1 else 0 end)
                + (case when s.total_social_amenities > 0 then 1 else 0 end)
                + (case when c.cooling_features_count > 0 then 1 else 0 end)
            ) as required_indicators_available,
            3 as required_indicators_total,
            3 - (
                (case when t.stop_count > 0 then 1 else 0 end)
                + (case when s.total_social_amenities > 0 then 1 else 0 end)
                + (case when c.cooling_features_count > 0 then 1 else 0 end)
            ) as missing_indicator_count,
            round(
                100 * (
                    (
                        (case when t.stop_count > 0 then 1 else 0 end)
                        + (case when s.total_social_amenities > 0 then 1 else 0 end)
                        + (case when c.cooling_features_count > 0 then 1 else 0 end)
                    )::numeric / 3
                ),
                2
            ) as data_quality_score,
            'MVP quality score based on availability of transport, social, and cooling/green indicators.'
        from mart.dim_city_parts d
        join mart.fact_transport_access t on d.city_part_id = t.city_part_id
        join mart.fact_social_infrastructure s on d.city_part_id = s.city_part_id
        join mart.fact_cooling_access c on d.city_part_id = c.city_part_id
        """,
        """
        insert into mart.fact_urban_comfort_score
            (city_part_id, cooling_score, transport_score, social_infrastructure_score,
             data_quality_score, urban_comfort_score, comfort_rank, weakest_dimension, strongest_dimension)
        with score_inputs as (
            select
                d.city_part_id,
                c.cooling_score,
                t.transport_score,
                s.social_infrastructure_score,
                q.data_quality_score,
                round(
                    0.35 * c.cooling_score
                    + 0.30 * t.transport_score
                    + 0.25 * s.social_infrastructure_score
                    + 0.10 * q.data_quality_score,
                    2
                ) as urban_comfort_score
            from mart.dim_city_parts d
            join mart.fact_cooling_access c on d.city_part_id = c.city_part_id
            join mart.fact_transport_access t on d.city_part_id = t.city_part_id
            join mart.fact_social_infrastructure s on d.city_part_id = s.city_part_id
            join mart.fact_data_quality q on d.city_part_id = q.city_part_id
        ),
        ranked as (
            select
                *,
                rank() over (order by urban_comfort_score desc) as comfort_rank
            from score_inputs
        )
        select
            city_part_id,
            cooling_score,
            transport_score,
            social_infrastructure_score,
            data_quality_score,
            urban_comfort_score,
            comfort_rank,
            case least(cooling_score, transport_score, social_infrastructure_score, data_quality_score)
                when cooling_score then 'Cooling / Green Access'
                when transport_score then 'Public Transport Access'
                when social_infrastructure_score then 'Social Infrastructure Access'
                else 'Data Quality'
            end as weakest_dimension,
            case greatest(cooling_score, transport_score, social_infrastructure_score, data_quality_score)
                when cooling_score then 'Cooling / Green Access'
                when transport_score then 'Public Transport Access'
                when social_infrastructure_score then 'Social Infrastructure Access'
                else 'Data Quality'
            end as strongest_dimension
        from ranked
        """,
        """
        insert into metadata.etl_runs (run_name, status, rows_loaded, notes)
        select 'build_mart', 'success', count(*), 'Built first MVP mart and Urban Comfort Score.'
        from mart.fact_urban_comfort_score
        """,
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def main() -> None:
    engine = get_engine()
    apply_sql_files(engine)
    build_mart(engine)
    with engine.connect() as conn:
        row_count = conn.execute(text("select count(*) from mart.fact_urban_comfort_score")).scalar()
    print(f"Built mart Urban Comfort Scores for {row_count} city parts.")


if __name__ == "__main__":
    main()
