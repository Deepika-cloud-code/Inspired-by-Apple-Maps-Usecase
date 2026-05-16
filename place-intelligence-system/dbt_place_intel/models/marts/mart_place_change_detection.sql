{{ config(materialized='table') }}

with historical_businesses as (

    select
        source_record_id as history_source_record_id,

        normalized_business_name as historical_business_name,
        normalized_address as historical_address,
        normalized_city as historical_city,
        normalized_state as historical_state,
        normalized_postal_code as historical_postal_code,

        license_id as historical_license_id,
        license_status_code as historical_license_status_code,
        license_status_category as historical_license_status_category,
        source_says_active as historical_source_says_active,

        license_description as historical_license_description,
        business_activity as historical_business_activity,

        date_issued as historical_date_issued,
        license_term_start_date as historical_license_term_start_date,
        license_term_expiration_date as historical_license_term_expiration_date,
        license_status_change_date as historical_license_status_change_date,

        source_match_key as historical_source_match_key,

        md5(
            coalesce(normalized_address, '') || '|' ||
            coalesce(normalized_city, '') || '|' ||
            coalesce(normalized_state, '') || '|' ||
            coalesce(normalized_postal_code, '')
        ) as address_key

    from {{ ref('int_license_history_cleaned') }}

    where normalized_business_name is not null
      and normalized_business_name <> ''
      and normalized_address is not null
      and normalized_address <> ''

),

current_active_businesses as (

    select
        source_record_id as current_source_record_id,

        normalized_business_name as current_business_name,
        normalized_address as current_address,
        normalized_city as current_city,
        normalized_state as current_state,
        normalized_postal_code as current_postal_code,

        license_id as current_license_id,
        license_status_code as current_license_status_code,
        license_status_category as current_license_status_category,
        source_says_active as current_source_says_active,

        license_description as current_license_description,
        business_activity as current_business_activity,

        date_issued as current_date_issued,
        license_term_start_date as current_license_term_start_date,
        license_term_expiration_date as current_license_term_expiration_date,
        license_status_change_date as current_license_status_change_date,

        source_match_key as current_source_match_key,

        md5(
            coalesce(normalized_address, '') || '|' ||
            coalesce(normalized_city, '') || '|' ||
            coalesce(normalized_state, '') || '|' ||
            coalesce(normalized_postal_code, '')
        ) as address_key

    from {{ ref('int_current_active_license_cleaned') }}

    where normalized_business_name is not null
      and normalized_business_name <> ''
      and normalized_address is not null
      and normalized_address <> ''

),

external_sources as (

    select
        source_system as external_source_system,
        source_record_id as external_source_record_id,

        normalized_business_name as external_business_name,
        normalized_address as external_address,
        normalized_city as external_city,
        normalized_state as external_state,
        normalized_postal_code as external_postal_code,

        place_category as external_place_category,
        source_says_active as external_source_says_active,
        source_specific_evidence as external_source_specific_evidence,

        md5(
            coalesce(normalized_address, '') || '|' ||
            coalesce(normalized_city, '') || '|' ||
            coalesce(normalized_state, '') || '|' ||
            coalesce(normalized_postal_code, '')
        ) as address_key

    from {{ ref('int_all_place_sources') }}

    where source_system in ('yelp', 'openstreetmap')
      and normalized_business_name is not null
      and normalized_business_name <> ''
      and normalized_address is not null
      and normalized_address <> ''

),

history_vs_current as (

    select
        h.*,

        c.current_source_record_id,
        c.current_business_name,
        c.current_address,
        c.current_city,
        c.current_state,
        c.current_postal_code,
        c.current_license_id,
        c.current_license_status_code,
        c.current_license_status_category,
        c.current_source_says_active,
        c.current_license_description,
        c.current_business_activity,
        c.current_date_issued,
        c.current_license_term_start_date,
        c.current_license_term_expiration_date,
        c.current_license_status_change_date,
        c.current_source_match_key,

        similarity(h.historical_business_name, c.current_business_name) as history_current_name_similarity,

        case
            when c.current_source_record_id is null then 0
            else 1
        end as has_current_active_at_same_address,

        case
            when c.current_source_record_id is not null
                 and similarity(h.historical_business_name, c.current_business_name) >= 0.80
                then 1
            else 0
        end as same_business_still_active,

        case
            when c.current_source_record_id is not null
                 and similarity(h.historical_business_name, c.current_business_name) < 0.80
                then 1
            else 0
        end as different_business_now_at_same_address

    from historical_businesses h

    left join current_active_businesses c
        on h.address_key = c.address_key

),

history_current_external as (

    select
        hc.*,

        e.external_source_system,
        e.external_source_record_id,
        e.external_business_name,
        e.external_address,
        e.external_city,
        e.external_state,
        e.external_postal_code,
        e.external_place_category,
        e.external_source_says_active,
        e.external_source_specific_evidence,

        similarity(hc.historical_business_name, e.external_business_name) as history_external_name_similarity,
        similarity(coalesce(hc.historical_address, ''), coalesce(e.external_address, '')) as history_external_address_similarity,

        case
            when e.external_source_record_id is not null
                 and similarity(hc.historical_business_name, e.external_business_name) >= 0.80
                then 1
            else 0
        end as historical_business_found_in_external_source

    from history_vs_current hc

    left join external_sources e
        on hc.address_key = e.address_key

),

change_signals as (

    select
        historical_business_name,
        historical_address,
        historical_city,
        historical_state,
        historical_postal_code,

        min(historical_license_id) as historical_license_id,
        min(historical_license_status_code) as historical_license_status_code,
        min(historical_license_status_category) as historical_license_status_category,

        max(case when historical_source_says_active = true then 1 else 0 end) as historical_active_signal,
        max(case when historical_source_says_active = false then 1 else 0 end) as historical_inactive_signal,

        min(historical_license_description) as historical_license_description,
        min(historical_business_activity) as historical_business_activity,

        max(historical_date_issued) as latest_historical_date_issued,
        max(historical_license_term_expiration_date) as latest_historical_license_expiration_date,
        max(historical_license_status_change_date) as latest_historical_status_change_date,

        max(has_current_active_at_same_address) as has_current_active_at_same_address,
        max(same_business_still_active) as same_business_still_active,
        max(different_business_now_at_same_address) as different_business_now_at_same_address,

        max(current_business_name) filter (where different_business_now_at_same_address = 1) as replacement_business_name,
        max(current_license_id) filter (where different_business_now_at_same_address = 1) as replacement_license_id,
        max(current_license_description) filter (where different_business_now_at_same_address = 1) as replacement_license_description,

        max(historical_business_found_in_external_source) as historical_business_found_in_external_source,

        string_agg(
            distinct external_source_system,
            ', ' order by external_source_system
        ) filter (where historical_business_found_in_external_source = 1) as stale_external_sources,

        max(history_current_name_similarity) as best_history_current_name_similarity,
        max(history_external_name_similarity) as best_history_external_name_similarity,
        max(history_external_address_similarity) as best_history_external_address_similarity,

        string_agg(
            distinct
            'HISTORY: ' ||
            coalesce(historical_business_name, '') ||
            ' | ' ||
            coalesce(historical_address, '') ||
            ' | status=' ||
            coalesce(historical_license_status_code, '') ||

            case
                when current_business_name is not null then
                    ' --> CURRENT_AT_SAME_ADDRESS: ' ||
                    coalesce(current_business_name, '') ||
                    ' | similarity=' ||
                    coalesce(round(history_current_name_similarity::numeric, 3)::text, '')
                else
                    ' --> NO_CURRENT_ACTIVE_LICENSE_AT_SAME_ADDRESS'
            end ||

            case
                when external_business_name is not null then
                    ' --> EXTERNAL: ' ||
                    coalesce(external_source_system, '') ||
                    ' | ' ||
                    coalesce(external_business_name, '') ||
                    ' | similarity=' ||
                    coalesce(round(history_external_name_similarity::numeric, 3)::text, '')
                else
                    ''
            end,
            ' || '
        ) as evidence_summary

    from history_current_external

    group by
        historical_business_name,
        historical_address,
        historical_city,
        historical_state,
        historical_postal_code
),

final_change_detection as (

    select
        md5(
            coalesce(historical_business_name, '') || '|' ||
            coalesce(historical_address, '') || '|' ||
            coalesce(historical_city, '') || '|' ||
            coalesce(historical_state, '') || '|' ||
            coalesce(historical_postal_code, '')
        ) as place_change_id,

        *,

        case
            when historical_inactive_signal = 1
                 and has_current_active_at_same_address = 0
                 and historical_business_found_in_external_source = 1
                then 'historical_business_closed_but_external_source_still_shows_it'

            when historical_inactive_signal = 1
                 and different_business_now_at_same_address = 1
                 and historical_business_found_in_external_source = 1
                then 'old_business_replaced_but_external_source_may_be_stale'

            when historical_inactive_signal = 1
                 and different_business_now_at_same_address = 1
                then 'old_business_replaced_by_new_business'

            when historical_inactive_signal = 1
                 and has_current_active_at_same_address = 0
                then 'historical_business_likely_closed'

            when historical_active_signal = 1
                 and same_business_still_active = 1
                then 'business_has_historical_continuity'

            when historical_active_signal = 1
                 and different_business_now_at_same_address = 1
                then 'same_address_has_multiple_active_or_recent_businesses_needs_review'

            else 'change_status_unknown'
        end as change_detection_status,

        case
            when historical_inactive_signal = 1
                 and has_current_active_at_same_address = 0
                then 'closure_signal_present'
            else 'no_clear_closure_signal'
        end as closure_signal,

        case
            when different_business_now_at_same_address = 1
                then 'replacement_signal_present'
            else 'no_replacement_signal'
        end as replacement_signal,

        case
            when historical_inactive_signal = 1
                 and historical_business_found_in_external_source = 1
                then 'external_source_may_be_stale'
            else 'no_clear_external_staleness_signal'
        end as external_staleness_signal,

        case
            when historical_inactive_signal = 1
                 and different_business_now_at_same_address = 1
                 and historical_business_found_in_external_source = 1
                then 'high_priority_review'

            when historical_inactive_signal = 1
                 and historical_business_found_in_external_source = 1
                then 'medium_priority_review'

            when historical_inactive_signal = 1
                 and different_business_now_at_same_address = 1
                then 'medium_confidence'

            when historical_active_signal = 1
                 and same_business_still_active = 1
                then 'high_confidence'

            else 'low_confidence'
        end as confidence_level,

        case
            when historical_inactive_signal = 1
                 and different_business_now_at_same_address = 1
                 and historical_business_found_in_external_source = 1
                then 'review_old_business_and_external_listing'

            when historical_inactive_signal = 1
                 and historical_business_found_in_external_source = 1
                then 'review_external_listing_for_possible_staleness'

            when historical_inactive_signal = 1
                 and different_business_now_at_same_address = 1
                then 'mark_old_business_as_replaced'

            when historical_inactive_signal = 1
                 and has_current_active_at_same_address = 0
                then 'mark_old_business_as_likely_closed'

            when historical_active_signal = 1
                 and same_business_still_active = 1
                then 'keep_business_active_with_history_support'

            else 'store_as_change_signal_for_later_review'
        end as recommended_action

    from change_signals
)

select
    place_change_id,

    historical_business_name,
    historical_address,
    historical_city,
    historical_state,
    historical_postal_code,

    historical_license_id,
    historical_license_status_code,
    historical_license_status_category,
    historical_active_signal,
    historical_inactive_signal,

    historical_license_description,
    historical_business_activity,

    latest_historical_date_issued,
    latest_historical_license_expiration_date,
    latest_historical_status_change_date,

    has_current_active_at_same_address,
    same_business_still_active,
    different_business_now_at_same_address,

    replacement_business_name,
    replacement_license_id,
    replacement_license_description,

    historical_business_found_in_external_source,
    stale_external_sources,

    best_history_current_name_similarity,
    best_history_external_name_similarity,
    best_history_external_address_similarity,

    change_detection_status,
    closure_signal,
    replacement_signal,
    external_staleness_signal,
    confidence_level,
    recommended_action,

    evidence_summary

from final_change_detection