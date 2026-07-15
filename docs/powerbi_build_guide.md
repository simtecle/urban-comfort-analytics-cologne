# Power BI Build Guide

This guide assumes Power BI Desktop only. Power BI Pro or Power BI Service is not required for the MVP.

## 1. Before Opening Power BI

Run the validation scripts from the repository root:

```bash
python scripts/check_db_connection.py
python scripts/validate_pipeline_load.py
python scripts/validate_mart.py
python scripts/export_city_parts_geojson.py
python scripts/validate_geojson_export.py
```

Expected results:

- 86 city parts in staging and mart
- 86 GeoJSON features
- 3 Power BI views available in `mart`

## 2. Connect Power BI Desktop To Supabase

In Power BI Desktop:

1. Select **Get data**.
2. Choose **PostgreSQL database**.
3. Enter the Supabase Session Pooler host as the server.
4. Enter database name `postgres`.
5. Choose **Import** mode.
6. Use **Database** authentication.
7. Enter the Supabase database user and password from your local `.env`.
8. Load these views:
   - `mart.v_powerbi_city_part_overview`
   - `mart.v_powerbi_score_breakdown`
   - `mart.v_powerbi_data_quality`

Do not load `raw` tables into the report.

## 3. Model Setup

Create relationships:

| From | To | Cardinality | Filter |
| --- | --- | --- | --- |
| `v_powerbi_city_part_overview[city_part_id]` | `v_powerbi_score_breakdown[city_part_id]` | One-to-many | Single |
| `v_powerbi_city_part_overview[city_part_id]` | `v_powerbi_data_quality[city_part_id]` | One-to-one | Single |

Set these columns to **Do not summarize**:

- `city_part_id`
- `city_part_name`
- `borough_name`
- `weakest_dimension`
- `strongest_dimension`
- `dimension_name`

## 4. Suggested Measures

Create these DAX measures:

```DAX
Average Urban Comfort Score = AVERAGE(v_powerbi_city_part_overview[urban_comfort_score])

Highest Score = MAX(v_powerbi_city_part_overview[urban_comfort_score])

Lowest Score = MIN(v_powerbi_city_part_overview[urban_comfort_score])

City Part Count = DISTINCTCOUNT(v_powerbi_city_part_overview[city_part_id])

Average Transport Score = AVERAGE(v_powerbi_city_part_overview[transport_score])

Average Cooling Score = AVERAGE(v_powerbi_city_part_overview[cooling_score])

Average Social Infrastructure Score = AVERAGE(v_powerbi_city_part_overview[social_infrastructure_score])
```

## 5. Report Pages

### Executive Overview

Visuals:

- KPI card: Average Urban Comfort Score
- KPI card: highest score
- KPI card: lowest score
- Bar chart: top 10 Stadtteile by score
- Bar chart: bottom 10 Stadtteile by score
- Column chart: average score by borough
- Text box: score is relative and method-based

### Score Explorer

Visuals:

- Slicer: city part name
- Card: rank
- Card: urban comfort score
- Bar chart: selected Stadtteil score breakdown by dimension
- Table: strongest and weakest dimension

### Mobility Access

Visuals:

- Bar chart: stops per km2 by Stadtteil
- Stacked bar: bus stop count vs Stadtbahn stop count
- Table: top and bottom transport access Stadtteile

### Social Infrastructure

Visuals:

- Clustered bar: schools, doctors, pharmacies, libraries
- Bar chart: social amenities per km2
- Table: total social amenities and score

### Cooling / Green Access

Visuals:

- Bar chart: cooling features per km2
- Stacked bar: parks, fountains, drinking water
- Table: weakest cooling access Stadtteile

### Data Quality & Method

Visuals/content:

- Data quality score table
- Missing indicator count
- Known unmatched records
- Score weights
- Data source and limitation notes

### Recommendations

Visuals/content:

- Table: low-score Stadtteile with weakest dimension
- Text boxes: recommended next investigation by weakness type
- Note: recommendations are analytical prompts, not official planning decisions

## 6. Shape Map

Use only after the core pages work.

1. Add a **Shape map** visual.
2. In Format visual / Map settings, choose **Custom map**.
3. Load `qgis/exports/cologne_city_parts.geojson`.
4. Use `city_part_id` as the location key.
5. Use `urban_comfort_score` as color saturation.
6. Use **View map type key** to confirm that map keys match `city_part_id`.

If matching fails, finish the dashboard with bar charts first and debug the map later.

## 7. Save And Export

Save the report as:

```text
powerbi/urban_comfort_dashboard.pbix
```

Export screenshots to:

```text
powerbi/screenshots/
```

Do not include credentials or connection dialogs in screenshots.
