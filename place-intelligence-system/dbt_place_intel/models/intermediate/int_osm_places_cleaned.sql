with base as (

    select
        -- source identity
        'openstreetmap' as source_system,
        'map_poi' as source_type,
        cast(osm_id as text) as source_record_id,

        -- common matching fields
        normalized_business_name,
        normalized_address,
        normalized_city,
        normalized_state,
        normalized_postal_code,
        cast(latitude as text) as latitude,
        cast(longitude as text) as longitude,

        -- common category field
        place_category,

        -- activity signal
        source_says_active,

        -- OSM-specific evidence columns
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
        raw_properties,
        raw_geometry,

        -- matching key for later comparison
        md5(
            coalesce(normalized_business_name, '') || '|' ||
            coalesce(normalized_address, '') || '|' ||
            coalesce(normalized_city, '') || '|' ||
            coalesce(normalized_state, '') || '|' ||
            coalesce(normalized_postal_code, '')
        ) as source_match_key

    from {{ ref('stg_osm_places') }}

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
                place_category
            order by
                osm_id desc
        ) as duplicate_rank

    from base
)

select
    *
from deduped
where duplicate_rank = 1