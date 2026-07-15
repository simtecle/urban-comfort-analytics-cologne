# Data Sources

The MVP targets all 86 Cologne Stadtteile. The source strategy is official open data where practical, plus OpenStreetMap where it provides the most complete point-of-interest and green-space coverage.

## Source Registry

| Source ID | Source | Use | License | Retrieval |
| --- | --- | --- | --- | --- |
| `cologne_city_parts_osm` | OpenStreetMap administrative boundary relations | Stadtteil boundaries for spatial joins | ODbL | Overpass API |
| `kvb_stops` | Haltestellen Stadtbahn und Bus KVB Koeln | Public transport access | Datenlizenz Deutschland Zero 2.0 | Offene Daten Koeln download |
| `osm_social_amenities` | OpenStreetMap amenities | Schools, doctors, pharmacies, libraries | ODbL | Overpass API |
| `osm_cooling_green` | OpenStreetMap green and cooling proxies | Parks, green spaces, drinking water, fountains | ODbL | Overpass API |

## KVB Stops

Portal page:

<https://offenedaten-koeln.de/dataset/haltestellen-stadtbahn-und-bus-kvb-koeln>

Direct CSV endpoint used by the extraction script:

<https://data.webservice-kvb.koeln/service/opendata/haltestellen/csv>

The portal describes the dataset as KVB Stadtbahn and bus stops including operating area and lines.

## OpenStreetMap / Overpass

Overpass endpoint:

<https://overpass-api.de/api/interpreter>

OSM data must be credited to OpenStreetMap contributors and identified as ODbL-licensed data in public documentation and dashboard notes.

Extract OSM datasets one at a time:

```bash
python scripts/extract_osm_amenities.py --dataset social_amenities
python scripts/extract_osm_amenities.py --dataset cooling_green
python scripts/extract_osm_amenities.py --dataset city_parts
```

The MVP should not download full OSM extracts. It should query only Cologne and only the tags needed for the current indicator group.

## Storage Strategy

Use a hybrid strategy:

1. Query APIs or open-data endpoints for targeted Cologne-only datasets.
2. Store raw snapshots under `data/raw/` for reproducibility.
3. Load only useful normalized rows into Supabase.
4. Build later Power BI tables from aggregated `mart` views, not raw source data.

## Known Risks

- OSM city-part boundary relations must be checked before scoring.
- OSM amenity completeness varies by area and mapper activity.
- KVB source records include some points outside the matched Cologne city-part polygons.
- The first MVP should document data quality visibly instead of hiding missing or uncertain data.

## Current Loaded Volumes

| Dataset | Loaded rows |
| --- | ---: |
| Cologne city parts | 86 |
| KVB stops | 2,156 |
| OSM social amenities | 1,094 |
| OSM cooling/green features | 519 |

Known unmatched records:

- 97 KVB stops without city-part assignment
- 1 OSM feature without city-part assignment
