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
    source_match_key,

    jsonb_build_object(
        'license_id', license_id,
        'account_number', account_number,
        'site_number', site_number,
        'legal_name', legal_name,
        'doing_business_as_name', doing_business_as_name,
        'license_status', license_status,
        'license_status_code', license_status_code,
        'license_status_category', license_status_category,
        'license_description', license_description,
        'business_activity', business_activity,
        'date_issued', date_issued,
        'license_term_start_date', license_term_start_date,
        'license_term_expiration_date', license_term_expiration_date,
        'address', address,
        'city', city,
        'state', state,
        'zip_code', zip_code,
        'latitude', latitude,
        'longitude', longitude
    ) as source_specific_evidence

from {{ ref('int_current_active_license_cleaned') }}

union all

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
    source_match_key,

    jsonb_build_object(
        'license_id', license_id,
        'account_number', account_number,
        'site_number', site_number,
        'legal_name', legal_name,
        'doing_business_as_name', doing_business_as_name,
        'license_status', license_status,
        'license_status_code', license_status_code,
        'license_status_category', license_status_category,
        'license_description', license_description,
        'business_activity', business_activity,
        'date_issued', date_issued,
        'license_term_start_date', license_term_start_date,
        'license_term_expiration_date', license_term_expiration_date,
        'address', address,
        'city', city,
        'state', state,
        'zip_code', zip_code,
        'latitude', latitude,
        'longitude', longitude
    ) as source_specific_evidence

from {{ ref('int_license_history_cleaned') }}

union all

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
    source_match_key,

    jsonb_build_object(
        'osm_id', osm_id,
        'name', name,
        'amenity', amenity,
        'shop', shop,
        'tourism', tourism,
        'house_number', house_number,
        'street', street,
        'phone', phone,
        'website', website,
        'opening_hours', opening_hours,
        'raw_properties', raw_properties,
        'raw_geometry', raw_geometry,
        'latitude', latitude,
        'longitude', longitude
    ) as source_specific_evidence

from {{ ref('int_osm_places_cleaned') }}

union all

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
    source_match_key,

    jsonb_build_object(
        'business_id', business_id,
        'name', name,
        'address', address,
        'city', city,
        'state', state,
        'postal_code', postal_code,
        'stars', stars,
        'review_count', review_count,
        'is_open', is_open,
        'yelp_open_status', yelp_open_status,
        'categories', categories,
        'hours', hours,
        'attributes', attributes,
        'latitude', latitude,
        'longitude', longitude
    ) as source_specific_evidence

from {{ ref('int_yelp_businesses_cleaned') }}