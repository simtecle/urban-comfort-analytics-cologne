# Methodology

## Analytical Unit

The MVP analyzes 86 Cologne city parts (`Stadtteile`). The project does not evaluate individual addresses, buildings, or parcels.

## Indicator Groups

The first version uses four score components:

| Dimension | Current indicator basis | Weight |
| --- | --- | ---: |
| Cooling / Green Access | Parks, fountains, drinking water per km2 | 35% |
| Public Transport Access | KVB stops per km2 | 30% |
| Social Infrastructure Access | Schools, doctors, pharmacies, libraries per km2 | 25% |
| Data Quality | Availability of required indicator groups | 10% |

## Normalization

Positive indicators use min-max normalization across the 86 city parts:

```text
normalized_score = 100 * (value - minimum_value) / (maximum_value - minimum_value)
```

This makes each sub-score relative to the current Cologne dataset.

## Final Score

```text
Urban Comfort Score =
0.35 * Cooling Score
+ 0.30 * Transport Score
+ 0.25 * Social Infrastructure Score
+ 0.10 * Data Quality Score
```

## Interpretation

| Score Range | Interpretation |
| --- | --- |
| 0-39 | Low relative urban comfort |
| 40-59 | Moderate relative urban comfort |
| 60-79 | Good relative urban comfort |
| 80-100 | High relative urban comfort |

The score is transparent and reproducible, but it is not an official city ranking or scientific urban climate model.

## Data Quality Treatment

Known current validation results:

- 86 city-part geometries loaded
- 0 missing city-part geometries
- 0 invalid city-part geometries
- 97 KVB stop records without city-part assignment
- 1 OSM feature without city-part assignment

These issues are not hidden. They should be shown on the Data Quality & Method page in Power BI.

## Version 1 Boundary

The MVP intentionally avoids:

- live refresh
- full OSM extracts
- detailed pedestrian network travel time
- heat raster modeling
- noise exposure modeling
- rent or real estate prediction
