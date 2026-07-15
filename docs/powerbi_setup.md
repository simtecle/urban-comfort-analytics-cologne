# Power BI Setup

Connect Power BI Desktop to Supabase PostgreSQL after the mart build succeeds.

For the complete click-by-click report build, use `docs/powerbi_build_guide.md`.

## Recommended Source Views

Load these views first:

- `mart.v_powerbi_city_part_overview`
- `mart.v_powerbi_score_breakdown`
- `mart.v_powerbi_data_quality`

Avoid connecting visuals directly to `raw` tables.

## First Report Pages

1. Executive Overview
   - Average Urban Comfort Score
   - Top 5 / bottom 5 Stadtteile
   - Score by borough
   - Short method note

2. Score Breakdown
   - Stadtteil selector
   - Dimension scores
   - Strongest and weakest dimension

3. Mobility Access
   - Stop count
   - Stops per km2
   - Bus vs Stadtbahn counts

4. Social Infrastructure
   - Schools, doctors, pharmacies, libraries
   - Total social amenities per km2

5. Cooling / Green Access
   - Parks
   - Fountains
   - Drinking water
   - Cooling features per km2

6. Data Quality & Method
   - Data sources
   - Missing indicators
   - Score weights
   - Limitations

## Important Notes

- The first score is relative to the 86 Cologne Stadtteile in the current dataset.
- OpenStreetMap-derived indicators may reflect mapping completeness.
- KVB stops outside Cologne city part boundaries are visible in validation output and should be documented as a limitation.
