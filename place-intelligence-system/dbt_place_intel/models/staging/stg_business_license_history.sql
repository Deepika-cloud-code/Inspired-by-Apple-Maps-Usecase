select
    id,
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
    ssa,
    latitude,
    longitude,
    location,

    lower(trim(coalesce(doing_business_as_name, legal_name))) as normalized_business_name,
    lower(trim(address)) as normalized_address,
    lower(trim(city)) as normalized_city,
    upper(trim(state)) as normalized_state,
    trim(zip_code) as normalized_postal_code,

    upper(trim(license_status)) as license_status_code,

    case
        when upper(trim(license_status)) = 'AAC' then 'active'
        when upper(trim(license_status)) in ('AAI', 'INQ', 'REA', 'REV') then 'inactive_or_historical'
        else 'unknown'
    end as license_status_category,

    case
        when upper(trim(license_status)) = 'AAC' then true
        else false
    end as source_says_active,

    'chicago_business_license_history' as source_system

from {{ source('raw', 'raw_business_license_history') }}