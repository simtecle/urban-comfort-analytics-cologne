# Limitations

## Interpretation Limits

Urban Comfort Analytics is a BI and portfolio project. It is not:

- an official city planning tool
- a legally binding district ranking
- a scientific climate model
- a real estate or rent prediction product
- a fully objective quality-of-life index

## Data Limits

- OpenStreetMap-derived indicators can reflect mapping completeness and community activity.
- KVB stop records include 97 points that do not currently match the loaded Cologne city-part polygons.
- One OSM feature does not currently match a city part.
- Cooling/green access is represented by simple features: parks, fountains, and drinking water.
- The MVP does not include tree canopy, land sealing, detailed heat exposure, or noise data.

## Method Limits

- Scores use min-max normalization, so results are relative to the current 86 city parts.
- Weighting is transparent but subjective.
- Density per km2 is a practical proxy and does not equal walking accessibility.
- Social infrastructure is counted by selected OSM categories only.
- Large city parts can behave differently from dense central areas because density-based scores reward concentration.

## Dashboard Communication

The Power BI dashboard should include these notes visibly:

- Scores compare city parts relative to the selected dataset.
- OSM indicators are useful proxies, not complete official inventories.
- Recommendations are prompts for further investigation, not policy decisions.
