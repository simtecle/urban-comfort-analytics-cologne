# Portfolio Summary

## Short Project Description

Urban Comfort Analytics Cologne is a Supabase/PostgreSQL and Power BI project that combines open mobility, social infrastructure, green/cooling, and data-quality indicators into a transparent Urban Comfort Score for 86 Cologne city parts.

## CV Bullets

- Built a database-backed Power BI analytics project using Supabase/PostgreSQL, PostGIS, Python ETL, and open urban data.
- Designed and implemented a transparent Urban Comfort Score for 86 Cologne city parts across transport, social infrastructure, cooling/green access, and data quality.
- Created reproducible extraction, loading, validation, and mart-building scripts for KVB and OpenStreetMap data.
- Prepared Power BI-ready mart views and a custom GeoJSON city-part export for spatial dashboard analysis.
- Documented methodology, assumptions, limitations, and data quality issues for portfolio and interview use.

## LinkedIn Description

Urban Comfort Analytics Cologne is a BI portfolio project that transforms fragmented open urban data into a structured, decision-oriented dashboard. The project uses Python ETL, Supabase/PostgreSQL, PostGIS, and Power BI Desktop to compare 86 Cologne city parts by transport access, social infrastructure, cooling/green access, and data quality.

The goal is not to create an official city ranking, but to demonstrate a realistic analytics workflow: data sourcing, geospatial preparation, database modeling, score design, Power BI reporting, and transparent limitation handling.

## Interview Talking Points

- Why the project uses city parts instead of address-level analysis
- How raw, staging, mart, and metadata schemas separate responsibilities
- Why Power BI connects to `mart` views instead of raw tables
- How min-max normalization and score weights work
- Why OSM-derived indicators require clear caveats
- How unmatched records become data quality signals instead of hidden errors

## Recruiter One-Minute Pitch

This project shows an end-to-end BI workflow. I used open data and OpenStreetMap, loaded and validated it with Python, modeled it in Supabase/PostgreSQL with PostGIS, calculated district-level comfort indicators, and prepared Power BI views for a portfolio dashboard. The project demonstrates technical BI implementation and business-oriented communication.
