{{ config(materialized='table') }}

with anchors as (

    select
        source_system as anchor_source_system,
        source_type as anchor_source_type,
        source_record_id as anchor_source_record_id,

        normalized_business_name as anchor_business_name,
        normalized_address as anchor_address,
        normalized_city as anchor_city,
        normalized_state as anchor_state,
        normalized_postal_code as anchor_postal_code,

        place_category as anchor_place_category,
        source_says_active as anchor_source_says_active,
        source_specific_evidence as anchor_source_specific_evidence

    from {{ ref('int_all_place_sources') }}

    where source_system = 'chicago_current_active_license'

),

fuzzy_matches as (

    select *
    from {{ ref('int_place_fuzzy_match_candidates') }}

),

anchor_with_matches as (

    select
        a.*,

        f.matched_source_system,
        f.matched_source_record_id,
        f.matched_business_name,
        f.matched_address,
        f.matched_city,
        f.matched_state,
        f.matched_postal_code,
        f.matched_place_category,
        f.matched_source_says_active,

        f.name_similarity,
        f.address_similarity,
        f.category_similarity,
        f.fuzzy_match_score,
        f.fuzzy_match_type,
        f.matched_source_specific_evidence

    from anchors a

    left join fuzzy_matches f
        on a.anchor_source_system = f.anchor_source_system
       and a.anchor_source_record_id = f.anchor_source_record_id

),

clustered as (

    select
        'PLACE_' || left(md5(anchor_source_system || '|' || anchor_source_record_id), 12) as place_cluster_id,

        anchor_source_system,
        anchor_source_record_id,

        min(anchor_business_name) as canonical_business_name,
        min(anchor_address) as canonical_address,
        min(anchor_city) as canonical_city,
        min(anchor_state) as canonical_state,
        min(anchor_postal_code) as canonical_postal_code,

        count(matched_source_record_id) + 1 as total_source_records,
        count(distinct matched_source_system) + 1 as matched_source_count,

        case
            when count(distinct matched_source_system) = 0
                then 'chicago_current_active_license'
            else string_agg(distinct matched_source_system, ', ' order by matched_source_system)
                 || ', chicago_current_active_license'
        end as matched_sources,

        1 as found_in_current_active_license,
        max(case when matched_source_system = 'yelp' then 1 else 0 end) as found_in_yelp,
        max(case when matched_source_system = 'openstreetmap' then 1 else 0 end) as found_in_osm,

        max(case when anchor_source_says_active = true then 1 else 0 end)
            + sum(case when matched_source_says_active = true then 1 else 0 end) as active_signal_count,

        max(case when anchor_source_says_active = false then 1 else 0 end)
            + sum(case when matched_source_says_active = false then 1 else 0 end) as inactive_signal_count,

        max(case when anchor_source_says_active is null then 1 else 0 end)
            + sum(case when matched_source_says_active is null and matched_source_record_id is not null then 1 else 0 end) as unknown_activity_signal_count,

        max(fuzzy_match_score) as best_fuzzy_match_score,
        min(fuzzy_match_score) as weakest_fuzzy_match_score,

        coalesce(
            string_agg(distinct fuzzy_match_type, ', ' order by fuzzy_match_type),
            'no_external_match'
        ) as fuzzy_match_types,

        coalesce(
            string_agg(
                distinct
                'NAME_MATCH: ' ||
                coalesce(anchor_business_name, '') ||
                ' = ' ||
                coalesce(matched_business_name, '') ||

                ' | ADDRESS_MATCH: ' ||
                coalesce(anchor_address, '') ||
                ' = ' ||
                coalesce(matched_address, '') ||

                ' | CITY_MATCH: ' ||
                coalesce(anchor_city, '') ||
                ' = ' ||
                coalesce(matched_city, '') ||

                ' | STATE_MATCH: ' ||
                coalesce(anchor_state, '') ||
                ' = ' ||
                coalesce(matched_state, '') ||

                ' | ZIP_MATCH: ' ||
                coalesce(anchor_postal_code, '') ||
                ' = ' ||
                coalesce(matched_postal_code, '') ||

                ' | NAME_SIMILARITY: ' ||
                round(name_similarity::numeric, 3)::text ||

                ' | ADDRESS_SIMILARITY: ' ||
                round(address_similarity::numeric, 3)::text ||

                ' | CATEGORY_SIMILARITY: ' ||
                round(category_similarity::numeric, 3)::text ||

                ' | MATCH_SCORE: ' ||
                round(fuzzy_match_score::numeric, 3)::text ||

                ' | MATCH_TYPE: ' ||
                coalesce(fuzzy_match_type, ''),
                ' || '
            ) filter (where matched_source_record_id is not null),
            'NO_EXTERNAL_MATCH_FOUND'
        ) as concatenated_values,

        jsonb_agg(
            jsonb_build_object(
                'matched_source_system', matched_source_system,
                'matched_source_record_id', matched_source_record_id,
                'matched_business_name', matched_business_name,
                'matched_address', matched_address,
                'name_similarity', name_similarity,
                'address_similarity', address_similarity,
                'fuzzy_match_score', fuzzy_match_score,
                'fuzzy_match_type', fuzzy_match_type,
                'matched_source_specific_evidence', matched_source_specific_evidence
            )
        ) filter (where matched_source_record_id is not null) as matched_source_evidence

    from anchor_with_matches

    group by
        anchor_source_system,
        anchor_source_record_id
)

select
    place_cluster_id,

    anchor_source_system,
    anchor_source_record_id,

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

    case
        when matched_source_count >= 3 then 'strong_fuzzy_cluster'
        when matched_source_count = 2 then 'medium_fuzzy_cluster'
        when matched_source_count = 1 then 'single_source_cluster'
        else 'unknown_cluster'
    end as cluster_strength,

    case
        when active_signal_count > 0 and inactive_signal_count = 0 then 'likely_active'
        when active_signal_count = 0 and inactive_signal_count > 0 then 'possible_closed_or_inactive'
        when active_signal_count > 0 and inactive_signal_count > 0 then 'conflicting_activity_signals'
        else 'unknown_activity_status'
    end as preliminary_place_status,

    matched_source_evidence

from clustered