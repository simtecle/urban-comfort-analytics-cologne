# Urban Comfort Analytics Cologne

Urban Comfort Analytics is a portfolio-ready BI project that evaluates urban comfort conditions across 86 Cologne city parts using open urban data, Supabase/PostgreSQL, Python ETL, PostGIS, and Power BI Desktop.

The project turns fragmented mobility, social infrastructure, green/cooling, and data-quality indicators into a transparent Urban Comfort Score and Power BI dashboard.

## Business Case

Urban comfort depends on several practical conditions: transport access, cooling and green infrastructure, everyday services, and data availability. These data points are usually spread across open-data portals and OpenStreetMap.

This project demonstrates how a BI analyst can turn that fragmented data into a structured, decision-oriented dashboard that helps compare districts, explain score drivers, and identify areas for deeper investigation.

## Current Status

- Supabase/PostgreSQL database created
- PostGIS enabled
- Raw, staging, mart, and metadata schemas created
- KVB stops loaded: 2,156 records
- OpenStreetMap city part boundaries loaded: 86 city parts
- OSM social amenities loaded: 1,094 records
- OSM cooling/green features loaded: 519 records
- Mart tables built for all 86 city parts
- First Urban Comfort Score calculated
- Power BI source views and city-part GeoJSON export prepared

## Architecture

```text
KVB Open Data + OpenStreetMap / Overpass
-> local raw snapshots in data/raw/
-> Python extraction and load scripts
-> Supabase PostgreSQL + PostGIS
-> raw, staging, mart, metadata schemas
-> Power BI Desktop views
-> Portfolio documentation and screenshots
```

## Data Model

Power BI should use the prepared `mart` views:

- `mart.v_powerbi_city_part_overview`
- `mart.v_powerbi_score_breakdown`
- `mart.v_powerbi_data_quality`

The current score uses:

- Cooling / Green Access: 35%
- Public Transport Access: 30%
- Social Infrastructure Access: 25%
- Data Quality: 10%

## First MVP Results

Top 5 city parts by the first MVP score:

| Rank | City part | Borough | Score |
| ---: | --- | --- | ---: |
| 1 | Altstadt-Nord | Innenstadt | 87.44 |
| 2 | Altstadt-Sued | Innenstadt | 80.87 |
| 3 | Neustadt/Sued | Innenstadt | 65.50 |
| 4 | Nippes | Nippes | 57.20 |
| 5 | Chorweiler | Chorweiler | 55.62 |

These scores are relative to the current 86-city-part dataset. They are not official planning results or a scientific quality-of-life index.

## Repository Structure

```text
sql/          Supabase/PostgreSQL schema, source, mart, and Power BI view SQL
scripts/      Python extraction, load, export, and validation scripts
data/         Local raw snapshots and sample data folders
qgis/         GeoJSON export for Power BI Shape Map / GIS validation
powerbi/      Power BI report file and screenshots
docs/         Setup, data model, methodology, data sources, and portfolio docs
presentation/ Optional final presentation export
```

## Setup

1. Create a Supabase project and enable PostGIS.
2. Copy `.env.example` to `.env` and fill in the Supabase connection details.
3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Run the SQL files in order or use the existing Supabase setup documented in `docs/supabase_setup.md`.
5. Run the pipeline:

```bash
python scripts/check_db_connection.py
python scripts/extract_kvb_stops.py
python scripts/extract_osm_amenities.py --dataset city_parts
python scripts/extract_osm_amenities.py --dataset social_amenities
python scripts/extract_osm_amenities.py --dataset cooling_green
python scripts/load_to_supabase.py
python scripts/build_mart.py
python scripts/export_city_parts_geojson.py
```

6. Validate:

```bash
python scripts/validate_pipeline_load.py
python scripts/validate_mart.py
python scripts/validate_geojson_export.py
```

## Power BI

Use Power BI Desktop in Import mode. The detailed build guide is in:

```text
docs/powerbi_build_guide.md
```

Expected report file:

```text
powerbi/urban_comfort_dashboard.pbix
```

Screenshots should be exported to:

```text
powerbi/screenshots/
```

## Limitations

- OpenStreetMap coverage may reflect mapping activity, not only real-world infrastructure.
- 97 KVB stop records are currently outside the 86 city-part polygons.
- 1 OSM feature is currently unmatched to a city part.
- Cooling/green access is represented by simple MVP proxies: parks, fountains, and drinking water.
- The score is relative and transparent, not objective or official.

## Portfolio Framing

This project is intended to demonstrate:

- BI workflow design
- PostgreSQL/Supabase modeling
- Python ETL
- Geospatial joins with PostGIS
- KPI and score methodology
- Power BI dashboard planning
- Data quality and limitation documentation
