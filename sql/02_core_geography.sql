create table if not exists raw.osm_city_parts (
    osm_type text not null,
    osm_id bigint not null,
    city_part_name text not null,
    admin_level text,
    raw_tags jsonb,
    geometry geometry(MultiPolygon, 4326),
    source_id text not null default 'cologne_city_parts_osm',
    ingested_at timestamptz not null default now(),
    primary key (osm_type, osm_id)
);

create table if not exists staging.city_parts (
    city_part_id text primary key,
    city_part_name text not null,
    borough_name text,
    osm_type text,
    osm_id bigint,
    area_km2 numeric,
    geometry geometry(MultiPolygon, 4326),
    geometry_valid boolean not null default false,
    source_id text not null,
    updated_at timestamptz not null default now()
);

create index if not exists idx_raw_osm_city_parts_geom
    on raw.osm_city_parts using gist (geometry);

create index if not exists idx_staging_city_parts_geom
    on staging.city_parts using gist (geometry);
