{{ config(materialized='table') }}

with source_records as (

    select
        source_system,
        source_type,
        source_record_id,

        normalized_business_name,
        normalized_address,
        normalized_city,
        normalized_state,
        normalized_postal_code,

        latitude,
        longitude,
        place_category,
        source_says_active,
        source_specific_evidence,

        left(regexp_replace(coalesce(normalized_postal_code, ''), '[^0-9]', '', 'g'), 5) as zip5,
        substring(normalized_address from '^[0-9]+') as street_number

    from {{ ref('int_all_place_sources') }}

    where normalized_business_name is not null
      and normalized_business_name <> ''
      and normalized_city is not null
      and normalized_state is not null
),

anchors as (

    select *
    from source_records
    where source_system = 'chicago_current_active_license'

),

external_sources as (

    select *
    from source_records
    where source_system in ('yelp', 'openstreetmap')

),

candidate_pairs as (

    select
        a.source_system as anchor_source_system,
        a.source_record_id as anchor_source_record_id,
        a.normalized_business_name as anchor_business_name,
        a.normalized_address as anchor_address,
        a.normalized_city as anchor_city,
        a.normalized_state as anchor_state,
        a.normalized_postal_code as anchor_postal_code,
        a.zip5 as anchor_zip5,
        a.street_number as anchor_street_number,
        a.place_category as anchor_place_category,
        a.source_says_active as anchor_source_says_active,

        b.source_system as matched_source_system,
        b.source_record_id as matched_source_record_id,
        b.normalized_business_name as matched_business_name,
        b.normalized_address as matched_address,
        b.normalized_city as matched_city,
        b.normalized_state as matched_state,
        b.normalized_postal_code as matched_postal_code,
        b.zip5 as matched_zip5,
        b.street_number as matched_street_number,
        b.place_category as matched_place_category,
        b.source_says_active as matched_source_says_active,

        similarity(a.normalized_business_name, b.normalized_business_name) as name_similarity,
        similarity(coalesce(a.normalized_address, ''), coalesce(b.normalized_address, '')) as address_similarity,
        similarity(coalesce(a.place_category, ''), coalesce(b.place_category, '')) as category_similarity,

        a.source_specific_evidence as anchor_source_specific_evidence,
        b.source_specific_evidence as matched_source_specific_evidence

    from anchors a

    inner join external_sources b
        on a.normalized_city = b.normalized_city
       and a.normalized_state = b.normalized_state
       and (
            a.zip5 = b.zip5
            or (
                a.street_number is not null
                and b.street_number is not null
                and a.street_number = b.street_number
            )
       )

),

scored_matches as (

    select
        *,

        case
            when name_similarity >= 0.85 and address_similarity >= 0.65 then 'strong_fuzzy_match'
            when name_similarity >= 0.75 and address_similarity >= 0.50 then 'medium_fuzzy_match'
            when name_similarity >= 0.85 and anchor_zip5 = matched_zip5 then 'name_zip_match'
            when name_similarity >= 0.70 and address_similarity >= 0.60 then 'address_supported_match'
            else 'weak_or_no_match'
        end as fuzzy_match_type,

        (
            (name_similarity * 0.50) +
            (address_similarity * 0.40) +
            (category_similarity * 0.10)
        ) as fuzzy_match_score

    from candidate_pairs
)

select
    md5(
        anchor_source_system || '|' ||
        anchor_source_record_id || '|' ||
        matched_source_system || '|' ||
        matched_source_record_id
    ) as fuzzy_match_id,

    anchor_source_system,
    anchor_source_record_id,
    anchor_business_name,
    anchor_address,
    anchor_city,
    anchor_state,
    anchor_postal_code,
    anchor_zip5,
    anchor_street_number,
    anchor_place_category,
    anchor_source_says_active,

    matched_source_system,
    matched_source_record_id,
    matched_business_name,
    matched_address,
    matched_city,
    matched_state,
    matched_postal_code,
    matched_zip5,
    matched_street_number,
    matched_place_category,
    matched_source_says_active,

    name_similarity,
    address_similarity,
    category_similarity,
    fuzzy_match_score,
    fuzzy_match_type,

    anchor_source_specific_evidence,
    matched_source_specific_evidence

from scored_matches

where fuzzy_match_type <> 'weak_or_no_match'