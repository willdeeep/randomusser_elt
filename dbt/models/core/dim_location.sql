with distinct_locations as (
    select distinct
        street_number,
        street_name,
        city,
        state,
        country,
        postcode,
        latitude,
        longitude,
        tz_offset
    from {{ ref('stg_randomuser') }}
)

select
    printf('%05d', row_number() over (order by street_number, street_name, postcode, city)) as location_id,
    street_number,
    street_name,
    city,
    state,
    country,
    postcode,
    latitude,
    longitude,
    tz_offset
from distinct_locations
