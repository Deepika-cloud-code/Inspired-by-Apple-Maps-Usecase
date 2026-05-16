/* ============================================================
   PLACE INTELLIGENCE SYSTEM - VALIDATION QUERIES
   Purpose:
   Validate staging, intermediate, fuzzy clustering, and mart outputs.

   How to use:
   Copy and run one section at a time in Adminer / Postgres.
   ============================================================ */


/* ============================================================
   1. RAW TABLE ROW COUNTS
   ============================================================ */

select
    'raw_business_license_history' as table_name,
    count(*) as row_count
from raw_business_license_history

union all

select
    'raw_current_active_licenses' as table_name,
    count(*) as row_count
from raw_current_active_licenses

union all

select
    'raw_osm_places' as table_name,
    count(*) as row_count
from raw_osm_places

union all

select
    'raw_yelp_businesses' as table_name,
    count(*) as row_count
from raw_yelp_businesses;


/* ============================================================
   2. STAGING MODEL ROW COUNTS
   ============================================================ */

select
    'stg_business_license_history' as model_name,
    count(*) as row_count
from stg_business_license_history

union all

select
    'stg_current_active_licenses' as model_name,
    count(*) as row_count
from stg_current_active_licenses

union all

select
    'stg_osm_places' as model_name,
    count(*) as row_count
from stg_osm_places

union all

select
    'stg_yelp_businesses' as model_name,
    count(*) as row_count
from stg_yelp_businesses;


/* ============================================================
   3. INTERMEDIATE MODEL ROW COUNTS
   ============================================================ */

select
    'int_license_history_cleaned' as model_name,
    count(*) as row_count
from int_license_history_cleaned

union all

select
    'int_current_active_license_cleaned' as model_name,
    count(*) as row_count
from int_current_active_license_cleaned

union all

select
    'int_osm_places_cleaned' as model_name,
    count(*) as row_count
from int_osm_places_cleaned

union all

select
    'int_yelp_businesses_cleaned' as model_name,
    count(*) as row_count
from int_yelp_businesses_cleaned

union all

select
    'int_all_place_sources' as model_name,
    count(*) as row_count
from int_all_place_sources;


/* ============================================================
   4. SOURCE DISTRIBUTION IN UNIFIED EVIDENCE TABLE
   ============================================================ */

select
    source_system,
    source_type,
    count(*) as row_count
from int_all_place_sources
group by
    source_system,
    source_type
order by row_count desc;


/* ============================================================
   5. ACTIVITY SIGNAL DISTRIBUTION BY SOURCE
   ============================================================ */

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


/* ============================================================
   6. FUZZY MATCH CANDIDATE COUNTS
   ============================================================ */

select
    fuzzy_match_type,
    count(*) as row_count
from int_place_fuzzy_match_candidates
group by fuzzy_match_type
order by row_count desc;


/* ============================================================
   7. PREVIEW FUZZY MATCH CANDIDATES
   ============================================================ */

select
    anchor_business_name,
    anchor_address,
    anchor_city,
    anchor_postal_code,
    matched_source_system,
    matched_business_name,
    matched_address,
    matched_city,
    matched_postal_code,
    name_similarity,
    address_similarity,
    category_similarity,
    fuzzy_match_score,
    fuzzy_match_type
from int_place_fuzzy_match_candidates
order by fuzzy_match_score desc
limit 50;


/* ============================================================
   8. CHECK ALL-ANCHOR FUZZY CLUSTERS
   This should include no_external_match rows.
   ============================================================ */

select
    fuzzy_match_types,
    count(*) as row_count
from int_place_fuzzy_clusters_all_anchors
group by fuzzy_match_types
order by row_count desc;


/* ============================================================
   9. COMPARE OLD FUZZY CLUSTERS VS ALL-ANCHOR CLUSTERS VS MART
   ============================================================ */

select
    'old_int_place_fuzzy_clusters' as table_name,
    count(*) as row_count
from int_place_fuzzy_clusters

union all

select
    'new_int_place_fuzzy_clusters_all_anchors' as table_name,
    count(*) as row_count
from int_place_fuzzy_clusters_all_anchors

union all

select
    'mart_place_status_summary' as table_name,
    count(*) as row_count
from mart_place_status_summary;


/* ============================================================
   10. ACTIVE STATUS MART - MAIN CATEGORY DISTRIBUTION
   ============================================================ */

select
    final_place_status,
    confidence_level,
    recommended_action,
    count(*) as row_count
from mart_place_status_summary
group by
    final_place_status,
    confidence_level,
    recommended_action
order by row_count desc;


/* ============================================================
   11. ACTIVE STATUS MART - FULL CATEGORY DISTRIBUTION
   ============================================================ */

select
    final_place_status,
    confidence_level,
    recommended_action,
    cluster_strength,
    preliminary_place_status,
    fuzzy_match_types,
    matched_sources,
    count(*) as row_count
from mart_place_status_summary
group by
    final_place_status,
    confidence_level,
    recommended_action,
    cluster_strength,
    preliminary_place_status,
    fuzzy_match_types,
    matched_sources
order by row_count desc;


/* ============================================================
   12. ACTIVE STATUS MART - CHECK NO EXTERNAL MATCH
   ============================================================ */

select
    final_place_status,
    confidence_level,
    recommended_action,
    fuzzy_match_types,
    matched_sources,
    count(*) as row_count
from mart_place_status_summary
where fuzzy_match_types = 'no_external_match'
group by
    final_place_status,
    confidence_level,
    recommended_action,
    fuzzy_match_types,
    matched_sources
order by row_count desc;


/* ============================================================
   13. ACTIVE STATUS MART - PREVIEW NO EXTERNAL MATCH ROWS
   ============================================================ */

select
    place_cluster_id,
    canonical_business_name,
    canonical_address,
    canonical_city,
    canonical_state,
    canonical_postal_code,
    matched_sources,
    fuzzy_match_types,
    final_place_status,
    confidence_level,
    recommended_action,
    concatenated_values
from mart_place_status_summary
where fuzzy_match_types = 'no_external_match'
limit 50;


/* ============================================================
   14. ACTIVE STATUS MART - PREVIEW OSM MATCHES
   ============================================================ */

select
    place_cluster_id,
    canonical_business_name,
    canonical_address,
    canonical_city,
    canonical_postal_code,
    matched_sources,
    fuzzy_match_types,
    best_fuzzy_match_score,
    final_place_status,
    confidence_level,
    recommended_action,
    concatenated_values
from mart_place_status_summary
where found_in_osm = 1
order by best_fuzzy_match_score desc nulls last
limit 50;


/* ============================================================
   15. ACTIVE STATUS MART - PREVIEW YELP MATCHES
   ============================================================ */

select
    place_cluster_id,
    canonical_business_name,
    canonical_address,
    canonical_city,
    canonical_postal_code,
    matched_sources,
    fuzzy_match_types,
    best_fuzzy_match_score,
    final_place_status,
    confidence_level,
    recommended_action,
    concatenated_values
from mart_place_status_summary
where found_in_yelp = 1
order by best_fuzzy_match_score desc nulls last
limit 50;


/* ============================================================
   16. CHANGE DETECTION MART - MAIN CATEGORY DISTRIBUTION
   ============================================================ */

select
    change_detection_status,
    closure_signal,
    replacement_signal,
    external_staleness_signal,
    confidence_level,
    recommended_action,
    count(*) as row_count
from mart_place_change_detection
group by
    change_detection_status,
    closure_signal,
    replacement_signal,
    external_staleness_signal,
    confidence_level,
    recommended_action
order by row_count desc;


/* ============================================================
   17. CHANGE DETECTION MART - LIKELY CLOSED EXAMPLES
   ============================================================ */

select
    historical_business_name,
    historical_address,
    historical_city,
    historical_state,
    historical_postal_code,
    historical_license_status_code,
    historical_license_status_category,
    latest_historical_license_expiration_date,
    has_current_active_at_same_address,
    change_detection_status,
    recommended_action,
    evidence_summary
from mart_place_change_detection
where change_detection_status = 'historical_business_likely_closed'
limit 50;


/* ============================================================
   18. CHANGE DETECTION MART - REPLACEMENT EXAMPLES
   ============================================================ */

select
    historical_business_name,
    historical_address,
    historical_city,
    historical_state,
    historical_postal_code,
    historical_license_status_code,
    replacement_business_name,
    replacement_license_description,
    best_history_current_name_similarity,
    change_detection_status,
    recommended_action,
    evidence_summary
from mart_place_change_detection
where change_detection_status = 'old_business_replaced_by_new_business'
order by best_history_current_name_similarity asc nulls last
limit 50;


/* ============================================================
   19. CHANGE DETECTION MART - CONTINUITY EXAMPLES
   ============================================================ */

select
    historical_business_name,
    historical_address,
    historical_license_status_code,
    same_business_still_active,
    best_history_current_name_similarity,
    change_detection_status,
    recommended_action,
    evidence_summary
from mart_place_change_detection
where change_detection_status = 'business_has_historical_continuity'
order by best_history_current_name_similarity desc nulls last
limit 50;


/* ============================================================
   20. CHANGE DETECTION MART - REVIEW CASES
   ============================================================ */

select
    historical_business_name,
    historical_address,
    historical_license_status_code,
    replacement_business_name,
    best_history_current_name_similarity,
    change_detection_status,
    confidence_level,
    recommended_action,
    evidence_summary
from mart_place_change_detection
where change_detection_status in (
    'same_address_has_multiple_active_or_recent_businesses_needs_review',
    'same_address_has_same_and_different_businesses_needs_review'
)
limit 50;


/* ============================================================
   21. CHANGE DETECTION MART - STALE EXTERNAL SOURCE CHECK
   ============================================================ */

select
    historical_business_name,
    historical_address,
    historical_license_status_code,
    replacement_business_name,
    historical_business_found_in_external_source,
    stale_external_sources,
    external_staleness_signal,
    change_detection_status,
    recommended_action,
    evidence_summary
from mart_place_change_detection
where external_staleness_signal = 'external_source_may_be_stale'
limit 50;


/* ============================================================
   22. CHANGE DETECTION MART - UNKNOWN CASES
   ============================================================ */

select
    historical_business_name,
    historical_address,
    historical_license_status_code,
    historical_license_status_category,
    historical_active_signal,
    historical_inactive_signal,
    has_current_active_at_same_address,
    same_business_still_active,
    different_business_now_at_same_address,
    historical_business_found_in_external_source,
    change_detection_status,
    recommended_action,
    evidence_summary
from mart_place_change_detection
where change_detection_status = 'change_status_unknown'
limit 50;


/* ============================================================
   23. CHECK DUPLICATES IN MART PLACE STATUS SUMMARY
   place_cluster_id should ideally be unique.
   ============================================================ */

select
    place_cluster_id,
    count(*) as duplicate_count
from mart_place_status_summary
group by place_cluster_id
having count(*) > 1
order by duplicate_count desc;


/* ============================================================
   24. CHECK DUPLICATES IN CHANGE DETECTION MART
   place_change_id should ideally be unique.
   ============================================================ */

select
    place_change_id,
    count(*) as duplicate_count
from mart_place_change_detection
group by place_change_id
having count(*) > 1
order by duplicate_count desc;


/* ============================================================
   25. CHECK NULLS IN IMPORTANT MART COLUMNS
   ============================================================ */

select
    'mart_place_status_summary' as table_name,
    count(*) filter (where place_cluster_id is null) as null_place_cluster_id,
    count(*) filter (where canonical_business_name is null) as null_business_name,
    count(*) filter (where final_place_status is null) as null_final_place_status,
    count(*) filter (where confidence_level is null) as null_confidence_level,
    count(*) filter (where recommended_action is null) as null_recommended_action
from mart_place_status_summary

union all

select
    'mart_place_change_detection' as table_name,
    count(*) filter (where place_change_id is null) as null_place_cluster_id,
    count(*) filter (where historical_business_name is null) as null_business_name,
    count(*) filter (where change_detection_status is null) as null_final_place_status,
    count(*) filter (where confidence_level is null) as null_confidence_level,
    count(*) filter (where recommended_action is null) as null_recommended_action
from mart_place_change_detection;


/* ============================================================
   26. TOP RECOMMENDED ACTIONS ACROSS BOTH MARTS
   ============================================================ */

select
    'mart_place_status_summary' as mart_name,
    recommended_action,
    count(*) as row_count
from mart_place_status_summary
group by recommended_action

union all

select
    'mart_place_change_detection' as mart_name,
    recommended_action,
    count(*) as row_count
from mart_place_change_detection
group by recommended_action
order by mart_name, row_count desc;


/* ============================================================
   27. SAMPLE RECORDS FOR RAG EVIDENCE GENERATION - STATUS MART
   ============================================================ */

select
    place_cluster_id,
    canonical_business_name,
    canonical_address,
    canonical_city,
    canonical_state,
    canonical_postal_code,
    final_place_status,
    confidence_level,
    recommended_action,
    matched_sources,
    fuzzy_match_types,
    concatenated_values
from mart_place_status_summary
limit 25;


/* ============================================================
   28. SAMPLE RECORDS FOR RAG EVIDENCE GENERATION - CHANGE MART
   ============================================================ */

select
    place_change_id,
    historical_business_name,
    historical_address,
    historical_city,
    historical_state,
    historical_postal_code,
    change_detection_status,
    closure_signal,
    replacement_signal,
    external_staleness_signal,
    confidence_level,
    recommended_action,
    evidence_summary
from mart_place_change_detection
limit 25;


/* ============================================================
   29. BUSINESS QUESTION: HOW MANY CURRENT ACTIVE BUSINESSES
       ARE MISSING EXTERNAL VALIDATION?
   ============================================================ */

select
    count(*) as missing_external_validation_count
from mart_place_status_summary
where recommended_action = 'officially_active_but_missing_external_sources';


/* ============================================================
   30. BUSINESS QUESTION: HOW MANY PLACES ARE SUPPORTED BY OSM?
   ============================================================ */

select
    count(*) as osm_supported_count
from mart_place_status_summary
where found_in_osm = 1;


/* ============================================================
   31. BUSINESS QUESTION: HOW MANY PLACES ARE SUPPORTED BY YELP?
   ============================================================ */

select
    count(*) as yelp_supported_count
from mart_place_status_summary
where found_in_yelp = 1;


/* ============================================================
   32. BUSINESS QUESTION: HOW MANY HISTORICAL BUSINESSES
       LIKELY CLOSED?
   ============================================================ */

select
    count(*) as likely_closed_count
from mart_place_change_detection
where change_detection_status = 'historical_business_likely_closed';


/* ============================================================
   33. BUSINESS QUESTION: HOW MANY OLD BUSINESSES WERE REPLACED?
   ============================================================ */

select
    count(*) as replaced_business_count
from mart_place_change_detection
where change_detection_status = 'old_business_replaced_by_new_business';


/* ============================================================
   34. BUSINESS QUESTION: HOW MANY BUSINESSES HAVE HISTORY CONTINUITY?
   ============================================================ */

select
    count(*) as historical_continuity_count
from mart_place_change_detection
where change_detection_status = 'business_has_historical_continuity';


/* ============================================================
   35. BUSINESS QUESTION: HOW MANY RECORDS NEED REVIEW?
   ============================================================ */

select
    recommended_action,
    count(*) as row_count
from mart_place_change_detection
where recommended_action like '%review%'
group by recommended_action
order by row_count desc;