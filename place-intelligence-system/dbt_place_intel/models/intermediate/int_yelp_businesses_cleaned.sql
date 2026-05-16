with base as (

    select
        -- source identity
        'yelp' as source_system,
        'commercial_business_listing' as source_type,
        cast(business_id as text) as source_record_id,

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

        -- Yelp-specific evidence columns
        business_id,
        name,
        address,
        city,
        state,
        postal_code,
        stars,
        review_count,
        is_open,
        yelp_open_status,
        categories,
        hours,
        attributes,
        raw_record,

        -- matching key for later comparison
        md5(
            coalesce(normalized_business_name, '') || '|' ||
            coalesce(normalized_address, '') || '|' ||
            coalesce(normalized_city, '') || '|' ||
            coalesce(normalized_state, '') || '|' ||
            coalesce(normalized_postal_code, '')
        ) as source_match_key

    from {{ ref('stg_yelp_businesses') }}

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
                normalized_postal_code
            order by
                review_count desc nulls last,
                stars desc nulls last,
                business_id
        ) as duplicate_rank

    from base
)

select
    *
from deduped
where duplicate_rank = 1