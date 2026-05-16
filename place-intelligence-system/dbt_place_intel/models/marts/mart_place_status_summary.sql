{{ config(materialized='table') }}

with fuzzy_clusters as (

    select
        place_cluster_id,

        canonical_business_name,
        canonical_address,
        canonical_city,
        canonical_state,
        canonical_postal_code,

        total_source_records,
        matched_source_count,
        matched_sources,

        found_in_current_active_license,
        found_in_yelp,
        found_in_osm,

        active_signal_count,
        inactive_signal_count,
        unknown_activity_signal_count,

        best_fuzzy_match_score,
        weakest_fuzzy_match_score,
        fuzzy_match_types,
        concatenated_values,

        cluster_strength,
        preliminary_place_status,
        matched_source_evidence

    from {{ ref('int_place_fuzzy_clusters_all_anchors') }}

),

final_status as (

    select
        *,

        case
            when active_signal_count > 0
                 and inactive_signal_count > 0
                then 'conflicting_signals_needs_review'

            when found_in_current_active_license = 1
                 and found_in_yelp = 1
                 and found_in_osm = 1
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                then 'verified_active'

            when found_in_current_active_license = 1
                 and found_in_yelp = 1
                 and found_in_osm = 0
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                then 'likely_active_with_yelp_support'

            when found_in_current_active_license = 1
                 and found_in_yelp = 0
                 and found_in_osm = 1
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                then 'likely_active_with_osm_support'

            when found_in_current_active_license = 1
                 and found_in_yelp = 0
                 and found_in_osm = 0
                then 'officially_active_but_missing_external_sources'

            when found_in_current_active_license = 0
                 and found_in_yelp = 1
                 and found_in_osm = 1
                then 'external_sources_present_but_missing_license'

            when found_in_current_active_license = 0
                 and found_in_yelp = 1
                 and found_in_osm = 0
                then 'yelp_only_needs_license_or_map_validation'

            when found_in_current_active_license = 0
                 and found_in_yelp = 0
                 and found_in_osm = 1
                then 'osm_only_needs_license_or_commercial_validation'

            when active_signal_count = 0
                 and inactive_signal_count > 0
                then 'possible_closed_or_inactive'

            when matched_source_count = 1
                then 'single_source_only_needs_more_evidence'

            else 'unknown_status'
        end as final_place_status,

        case
            when active_signal_count > 0
                 and inactive_signal_count > 0
                then 'review_required'

            when found_in_current_active_license = 1
                 and found_in_yelp = 1
                 and found_in_osm = 1
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                 and best_fuzzy_match_score >= 0.80
                then 'high_confidence'

            when found_in_current_active_license = 1
                 and found_in_yelp = 0
                 and found_in_osm = 0
                then 'low_confidence'

            when found_in_current_active_license = 1
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                 and matched_source_count >= 2
                then 'medium_confidence'

            when found_in_current_active_license = 0
                 and matched_source_count >= 2
                then 'medium_confidence_needs_license_check'

            when inactive_signal_count > 0
                 and active_signal_count = 0
                then 'medium_confidence'

            else 'low_confidence'
        end as confidence_level,

        case
            when active_signal_count > 0
                 and inactive_signal_count > 0
                then 'send_for_human_review_conflicting_signals'

            when found_in_current_active_license = 1
                 and found_in_yelp = 1
                 and found_in_osm = 1
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                 and best_fuzzy_match_score >= 0.80
                then 'approve_as_verified_active'

            when found_in_current_active_license = 1
                 and found_in_yelp = 1
                 and found_in_osm = 0
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                then 'keep_active_with_yelp_support'

            when found_in_current_active_license = 1
                 and found_in_yelp = 0
                 and found_in_osm = 1
                 and active_signal_count > 0
                 and inactive_signal_count = 0
                then 'active_but_missing_yelp_validation'

            when found_in_current_active_license = 1
                 and found_in_yelp = 0
                 and found_in_osm = 0
                then 'officially_active_but_missing_external_sources'

            when found_in_current_active_license = 0
                 and found_in_yelp = 1
                 and found_in_osm = 1
                then 'external_listing_needs_license_check'

            when found_in_current_active_license = 0
                 and found_in_yelp = 1
                 and found_in_osm = 0
                then 'yelp_listing_needs_license_and_map_validation'

            when found_in_current_active_license = 0
                 and found_in_yelp = 0
                 and found_in_osm = 1
                then 'osm_place_needs_license_and_commercial_validation'

            when active_signal_count = 0
                 and inactive_signal_count > 0
                then 'flag_as_possible_closure'

            else 'store_as_weak_signal'
        end as recommended_action

    from fuzzy_clusters
)

select
    place_cluster_id,

    canonical_business_name,
    canonical_address,
    canonical_city,
    canonical_state,
    canonical_postal_code,

    total_source_records,
    matched_source_count,
    matched_sources,

    found_in_current_active_license,
    found_in_yelp,
    found_in_osm,

    active_signal_count,
    inactive_signal_count,
    unknown_activity_signal_count,

    best_fuzzy_match_score,
    weakest_fuzzy_match_score,
    fuzzy_match_types,

    cluster_strength,
    preliminary_place_status,

    final_place_status,
    confidence_level,
    recommended_action,

    concatenated_values,
    matched_source_evidence

from final_status