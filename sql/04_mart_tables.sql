create table if not exists mart.dim_city_parts (
    city_part_id text primary key,
    city_part_name text not null,
    borough_name text,
    area_km2 numeric,
    geometry_available boolean not null default false,
    source_id text not null,
    updated_at timestamptz not null default now()
);

create table if not exists mart.fact_transport_access (
    city_part_id text primary key references mart.dim_city_parts(city_part_id),
    stop_count integer not null default 0,
    stops_per_km2 numeric,
    rail_stop_count integer not null default 0,
    bus_stop_count integer not null default 0,
    transport_score numeric,
    unmatched_source_count integer not null default 0,
    calculated_at timestamptz not null default now()
);

create table if not exists mart.fact_social_infrastructure (
    city_part_id text primary key references mart.dim_city_parts(city_part_id),
    schools_count integer not null default 0,
    doctors_count integer not null default 0,
    pharmacies_count integer not null default 0,
    libraries_count integer not null default 0,
    total_social_amenities integer not null default 0,
    social_amenities_per_km2 numeric,
    social_infrastructure_score numeric,
    calculated_at timestamptz not null default now()
);

create table if not exists mart.fact_cooling_access (
    city_part_id text primary key references mart.dim_city_parts(city_part_id),
    drinking_water_count integer not null default 0,
    fountain_count integer not null default 0,
    park_count integer not null default 0,
    cooling_features_count integer not null default 0,
    cooling_features_per_km2 numeric,
    cooling_score numeric,
    calculated_at timestamptz not null default now()
);

create table if not exists mart.fact_data_quality (
    city_part_id text primary key references mart.dim_city_parts(city_part_id),
    required_indicators_available integer not null,
    required_indicators_total integer not null,
    missing_indicator_count integer not null,
    data_quality_score numeric not null,
    notes text,
    calculated_at timestamptz not null default now()
);

create table if not exists mart.fact_urban_comfort_score (
    city_part_id text primary key references mart.dim_city_parts(city_part_id),
    cooling_score numeric,
    transport_score numeric,
    social_infrastructure_score numeric,
    data_quality_score numeric,
    urban_comfort_score numeric,
    comfort_rank integer,
    weakest_dimension text,
    strongest_dimension text,
    calculated_at timestamptz not null default now()
);
