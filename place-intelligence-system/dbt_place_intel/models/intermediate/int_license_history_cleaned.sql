with base as (

    select
        -- source identity
        'chicago_business_license_history' as source_system,
        'business_license_history' as source_type,
        cast(license_id as text) as source_record_id,

        -- common matching fields
        normalized_business_name,
        normalized_address,
        normalized_city,
        normalized_state,
        normalized_postal_code,
        cast(latitude as text) as latitude,
        cast(longitude as text) as longitude,

        -- common category field
        lower(trim(license_description)) as place_category,

        -- activity signal
        source_says_active,

        -- license-specific evidence columns
        license_id,
        account_number,
        site_number,
        legal_name,
        doing_business_as_name,
        address,
        city,
        state,
        zip_code,
        ward,
        precinct,
        ward_precinct,
        police_district,
        community_area,
        community_area_name,
        neighborhood,
        license_code,
        license_description,
        business_activity_id,
        business_activity,
        license_number,
        application_type,
        application_created_date,
        application_requirements_complete,
        payment_date,
        conditional_approval,
        license_term_start_date,
        license_term_expiration_date,
        license_approved_for_issuance,
        date_issued,
        license_status,
        license_status_change_date,
        license_status_code,
        license_status_category,
        ssa,
        location,

        -- matching key for later comparison
        md5(
            coalesce(normalized_business_name, '') || '|' ||
            coalesce(normalized_address, '') || '|' ||
            coalesce(normalized_city, '') || '|' ||
            coalesce(normalized_state, '') || '|' ||
            coalesce(normalized_postal_code, '')
        ) as source_match_key

    from {{ ref('stg_business_license_history') }}

    where normalized_business_name is not null
      and normalized_business_name <> ''
),

deduped as (

    select
        *,
        row_number() over (
            partition by
                normalized_business_name,
                normalized_address,
                normalized_city,
                normalized_state,
                normalized_postal_code,
                license_description,
                license_status_code
            order by
                date_issued desc nulls last,
                license_id desc
        ) as duplicate_rank

    from base
)

select
    *
from deduped
where duplicate_rank = 1