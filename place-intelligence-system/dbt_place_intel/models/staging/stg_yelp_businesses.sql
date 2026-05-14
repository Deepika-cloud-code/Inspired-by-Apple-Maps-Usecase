select
    business_id,
    name,
    address,
    city,
    state,
    postal_code,
    latitude,
    longitude,
    stars,
    review_count,
    is_open,
    categories,
    hours,
    attributes,
    raw_record,

    -- standardized fields for matching with Chicago licenses and OSM
    lower(trim(name)) as normalized_business_name,
    lower(trim(address)) as normalized_address,
    lower(trim(city)) as normalized_city,
    upper(trim(state)) as normalized_state,
    trim(postal_code) as normalized_postal_code,

    -- Yelp category field
    lower(trim(categories)) as place_category,

    -- readable Yelp open/closed status
    case
        when is_open = 1 then 'open'
        when is_open = 0 then 'closed'
        when is_open is null then 'missing_status'
        else 'unknown'
    end as yelp_open_status,

    -- boolean activity signal
    case
        when is_open = 1 then true
        when is_open = 0 then false
        else null
    end as source_says_active,

    'yelp' as source_system

from {{ source('raw', 'raw_yelp_businesses') }}

where name is not null
  and trim(name) <> ''