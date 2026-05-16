select count(*) from int_current_active_license_cleaned;
select count(*) from int_license_history_cleaned;
select count(*) from int_osm_places_cleaned;
select count(*) from int_yelp_businesses_cleaned;
select count(*) from int_all_place_sources;

select
    source_system,
    source_type,
    count(*) as row_count
from int_all_place_sources
group by
    source_system,
    source_type
order by row_count desc;

select
    source_system,
    source_says_active,
    count(*) as row_count
from int_all_place_sources
group by
    source_system,
    source_says_active
order by
    source_system,
    source_says_active;

select
    source_system,
    source_type,
    source_record_id,
    normalized_business_name,
    normalized_address,
    normalized_city,
    normalized_postal_code,
    place_category,
    source_says_active,
    source_specific_evidence
from int_all_place_sources
limit 20;   

select count(*)
from int_place_clusters;

select
    cluster_strength,
    count(*) as row_count
from int_place_clusters
group by cluster_strength
order by row_count desc;

select
    preliminary_place_status,
    count(*) as row_count
from int_place_clusters
group by preliminary_place_status
order by row_count desc;

select
    place_cluster_id,
    canonical_business_name,
    canonical_address,
    canonical_city,
    canonical_postal_code,
    matched_source_count,
    matched_sources,
    active_signal_count,
    inactive_signal_count,
    preliminary_place_status
from int_place_clusters
where matched_source_count >= 2
limit 50;