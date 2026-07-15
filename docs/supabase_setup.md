# Supabase Setup

This project uses Supabase Cloud as the central PostgreSQL database for the BI workflow.

## 1. Project

Create a Supabase project named `urban-comfort-analytics-cologne`.

Recommended settings:

- Region: EU, if available
- Database password: store securely outside Git
- RLS: keep disabled for internal MVP tables unless a future web app exposes user-specific data

## 2. PostGIS

Enable PostGIS in Supabase:

1. Open the Supabase project.
2. Go to Database / Extensions.
3. Enable `postgis`.
4. Use the default `extensions` schema when prompted.

Check it in the SQL Editor:

```sql
select postgis_full_version();
```

## 3. Foundation SQL

Run this file in the Supabase SQL Editor:

```text
sql/01_supabase_foundation.sql
```

It creates:

- `raw`
- `staging`
- `mart`
- `metadata`
- metadata tables
- MVP score weights
- initial source registry rows

## 4. Local Environment

Copy `.env.example` to `.env` and fill it locally.

Do not commit `.env`.

Recommended Supabase connection mode for local development:

- Session pooler
- SSL required
- Port `5432`

## 5. Local Connection Test

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python scripts/check_db_connection.py
```

Expected result:

- database and user shown without password
- four project schemas found
- PostGIS available
- four active score weights found

## 6. First Data Load: KVB Stops

Download the official KVB stops snapshot:

```bash
python scripts/extract_kvb_stops.py
```

Load the normalized raw rows into Supabase:

```bash
python scripts/load_to_supabase.py
```

Validate the load:

```bash
python scripts/validate_kvb_load.py
```

The raw CSV stays local under `data/raw/` and is ignored by Git.

## 7. OSM Extraction Rule

Run OSM extracts one dataset at a time:

```bash
python scripts/extract_osm_amenities.py --dataset social_amenities
python scripts/extract_osm_amenities.py --dataset cooling_green
python scripts/extract_osm_amenities.py --dataset city_parts
```

Do not download full OSM extracts for the MVP.
