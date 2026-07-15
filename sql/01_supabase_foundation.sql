create schema if not exists raw;
create schema if not exists staging;
create schema if not exists mart;
create schema if not exists metadata;

create table if not exists metadata.data_sources (
    source_id text primary key,
    source_name text not null,
    source_url text,
    source_owner text,
    license text,
    source_type text,
    retrieval_method text,
    notes text,
    created_at timestamptz not null default now(),
    last_checked_at date
);

create table if not exists metadata.etl_runs (
    etl_run_id uuid primary key default gen_random_uuid(),
    run_name text not null,
    status text not null,
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    rows_loaded integer,
    notes text
);

create table if not exists metadata.indicator_definitions (
    indicator_id text primary key,
    indicator_name text not null,
    dimension_name text not null,
    description text not null,
    unit text,
    positive_direction boolean not null default true,
    calculation_note text
);

create table if not exists metadata.score_weights (
    dimension_name text primary key,
    weight numeric not null check (weight >= 0 and weight <= 1),
    is_active boolean not null default true,
    notes text,
    updated_at timestamptz not null default now()
);

insert into metadata.score_weights (dimension_name, weight, notes)
values
    ('Cooling / Green Access', 0.35, 'Initial MVP weighting from PRD'),
    ('Public Transport Access', 0.30, 'Initial MVP weighting from PRD'),
    ('Social Infrastructure Access', 0.25, 'Initial MVP weighting from PRD'),
    ('Data Quality', 0.10, 'Initial MVP weighting from PRD')
on conflict (dimension_name) do update
set
    weight = excluded.weight,
    notes = excluded.notes,
    updated_at = now();

insert into metadata.data_sources
    (source_id, source_name, source_url, source_owner, license, source_type, retrieval_method, notes, last_checked_at)
values
    (
        'cologne_city_parts_osm',
        'Cologne city part boundaries from OpenStreetMap',
        'https://overpass-api.de/api/interpreter',
        'OpenStreetMap contributors',
        'Open Database License (ODbL)',
        'geospatial_boundaries',
        'overpass_api',
        'Used as first source for the 86 Stadtteile boundary layer; validate in QGIS before scoring.',
        current_date
    ),
    (
        'kvb_stops',
        'Haltestellen Stadtbahn und Bus KVB Koeln',
        'https://offenedaten-koeln.de/dataset/haltestellen-stadtbahn-und-bus-kvb-koeln',
        'KVB Koeln',
        'Datenlizenz Deutschland - Zero - Version 2.0',
        'mobility_points',
        'download_script',
        'Official KVB stops dataset from Offene Daten Koeln.',
        current_date
    ),
    (
        'osm_social_amenities',
        'Social infrastructure amenities from OpenStreetMap',
        'https://overpass-api.de/api/interpreter',
        'OpenStreetMap contributors',
        'Open Database License (ODbL)',
        'amenity_points',
        'overpass_api',
        'Schools, doctors, pharmacies, libraries and related amenities.',
        current_date
    ),
    (
        'osm_cooling_green',
        'Cooling and green infrastructure from OpenStreetMap',
        'https://overpass-api.de/api/interpreter',
        'OpenStreetMap contributors',
        'Open Database License (ODbL)',
        'environmental_points_or_polygons',
        'overpass_api',
        'Parks, green spaces, drinking water, fountains and related cooling proxies.',
        current_date
    )
on conflict (source_id) do update
set
    source_name = excluded.source_name,
    source_url = excluded.source_url,
    source_owner = excluded.source_owner,
    license = excluded.license,
    source_type = excluded.source_type,
    retrieval_method = excluded.retrieval_method,
    notes = excluded.notes,
    last_checked_at = excluded.last_checked_at;
