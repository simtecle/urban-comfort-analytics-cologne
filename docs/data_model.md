# Data Model

The current MVP data model has four layers:

| Schema | Purpose |
| --- | --- |
| `raw` | Normalized source snapshots loaded from local raw files |
| `staging` | Cleaned records with city part assignment |
| `mart` | Analytics-ready tables and Power BI views |
| `metadata` | Source registry, ETL runs, score weights, and indicator definitions |

## Current Pipeline

```text
KVB CSV / Overpass API
-> local snapshots in data/raw/
-> raw.kvb_stops, raw.osm_city_parts, raw.osm_amenities
-> staging.city_parts, staging.transport_stops, staging.amenities
-> mart dimensions, facts, score table, Power BI views
```

## Mart Tables

| Table | Grain | Purpose |
| --- | --- | --- |
| `mart.dim_city_parts` | One row per Cologne Stadtteil | Geography dimension for 86 city parts |
| `mart.fact_transport_access` | One row per Stadtteil | KVB stop counts and transport score |
| `mart.fact_social_infrastructure` | One row per Stadtteil | Schools, doctors, pharmacies, libraries |
| `mart.fact_cooling_access` | One row per Stadtteil | Parks, fountains, drinking water |
| `mart.fact_data_quality` | One row per Stadtteil | MVP completeness score |
| `mart.fact_urban_comfort_score` | One row per Stadtteil | Weighted final score and rank |

## Power BI Views

Use these views as the initial Power BI source objects:

- `mart.v_powerbi_city_part_overview`
- `mart.v_powerbi_score_breakdown`
- `mart.v_powerbi_data_quality`

## Current MVP Score

The first score uses density-based positive indicators:

- Transport: KVB stops per km2
- Social infrastructure: selected amenities per km2
- Cooling / green: selected cooling and park features per km2
- Data quality: availability of the three required indicator groups

Weights:

- Cooling / Green Access: 35%
- Public Transport Access: 30%
- Social Infrastructure Access: 25%
- Data Quality: 10%

This is a first transparent MVP score, not a final scientific index.
