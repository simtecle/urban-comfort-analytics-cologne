create table if not exists raw.kvb_stops (
    source_record_id text primary key,
    stop_name text,
    stop_area text,
    line_info text,
    raw_payload jsonb not null,
    latitude numeric,
    longitude numeric,
    geom geometry(Point, 4326),
    source_id text not null default 'kvb_stops',
    ingested_at timestamptz not null default now()
);

create table if not exists raw.osm_amenities (
    osm_type text not null,
    osm_id bigint not null,
    amenity_group text not null,
    amenity_type text,
    amenity_name text,
    raw_tags jsonb,
    latitude numeric,
    longitude numeric,
    geom geometry(Point, 4326),
    source_id text not null,
    ingested_at timestamptz not null default now(),
    primary key (osm_type, osm_id, amenity_group)
);

create table if not exists staging.transport_stops (
    stop_id text primary key,
    stop_name text,
    stop_area text,
    line_info text,
    city_part_id text references staging.city_parts(city_part_id),
    geom geometry(Point, 4326),
    source_id text not null default 'kvb_stops',
    updated_at timestamptz not null default now()
);

create table if not exists staging.amenities (
    amenity_id text primary key,
    amenity_group text not null,
    amenity_type text,
    amenity_name text,
    city_part_id text references staging.city_parts(city_part_id),
    geom geometry(Point, 4326),
    source_id text not null,
    updated_at timestamptz not null default now()
);

create index if not exists idx_raw_kvb_stops_geom
    on raw.kvb_stops using gist (geom);

create index if not exists idx_raw_osm_amenities_geom
    on raw.osm_amenities using gist (geom);

create index if not exists idx_staging_transport_stops_geom
    on staging.transport_stops using gist (geom);

create index if not exists idx_staging_amenities_geom
    on staging.amenities using gist (geom);
