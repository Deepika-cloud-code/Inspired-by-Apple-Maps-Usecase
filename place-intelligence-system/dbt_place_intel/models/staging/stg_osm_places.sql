select
    osm_id,
    name,
    amenity,
    shop,
    tourism,
    house_number,
    street,
    city,
    state,
    postcode,
    phone,
    website,
    opening_hours,
    latitude,
    longitude,
    raw_properties,
    raw_geometry,

    -- standardized fields for matching with Chicago licenses and Yelp
    lower(trim(name)) as normalized_business_name,

    lower(
        trim(
            concat(
                coalesce(house_number, ''),
                case
                    when house_number is not null and street is not null then ' '
                    else ''
                end,
                coalesce(street, '')
            )
        )
    ) as normalized_address,

    lower(trim(city)) as normalized_city,
    upper(trim(state)) as normalized_state,
    trim(postcode) as normalized_postal_code,

    -- common category field
    case
        when amenity is not null and trim(amenity) <> '' then lower(trim(amenity))
        when shop is not null and trim(shop) <> '' then lower(trim(shop))
        when tourism is not null and trim(tourism) <> '' then lower(trim(tourism))
        else null
    end as place_category,

    -- OSM shows map presence, but does not reliably mean active/open
    'openstreetmap' as source_system,
    null::boolean as source_says_active

from {{ source('raw', 'raw_osm_places') }}

where name is not null
  and trim(name) <> ''