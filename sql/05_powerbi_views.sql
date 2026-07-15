create or replace view mart.v_powerbi_city_part_overview as
select
    d.city_part_id,
    d.city_part_name,
    d.borough_name,
    d.area_km2,
    s.urban_comfort_score,
    s.comfort_rank,
    s.weakest_dimension,
    s.strongest_dimension,
    s.cooling_score,
    s.transport_score,
    s.social_infrastructure_score,
    s.data_quality_score,
    t.stop_count,
    t.stops_per_km2,
    c.cooling_features_count,
    c.cooling_features_per_km2,
    si.total_social_amenities,
    si.social_amenities_per_km2,
    s.calculated_at
from mart.dim_city_parts d
left join mart.fact_urban_comfort_score s on d.city_part_id = s.city_part_id
left join mart.fact_transport_access t on d.city_part_id = t.city_part_id
left join mart.fact_cooling_access c on d.city_part_id = c.city_part_id
left join mart.fact_social_infrastructure si on d.city_part_id = si.city_part_id;

create or replace view mart.v_powerbi_score_breakdown as
select city_part_id, 'Cooling / Green Access' as dimension_name, cooling_score as score
from mart.fact_urban_comfort_score
union all
select city_part_id, 'Public Transport Access', transport_score
from mart.fact_urban_comfort_score
union all
select city_part_id, 'Social Infrastructure Access', social_infrastructure_score
from mart.fact_urban_comfort_score
union all
select city_part_id, 'Data Quality', data_quality_score
from mart.fact_urban_comfort_score;

create or replace view mart.v_powerbi_data_quality as
select
    d.city_part_id,
    d.city_part_name,
    d.borough_name,
    q.required_indicators_available,
    q.required_indicators_total,
    q.missing_indicator_count,
    q.data_quality_score,
    q.notes,
    t.unmatched_source_count as unmatched_transport_stop_count,
    q.calculated_at
from mart.dim_city_parts d
left join mart.fact_data_quality q on d.city_part_id = q.city_part_id
left join mart.fact_transport_access t on d.city_part_id = t.city_part_id;
