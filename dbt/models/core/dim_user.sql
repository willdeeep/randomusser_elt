-- dim_location dedupes on the address tuple, so that's the join key here rather than a
-- carried-through id: it's how two people at the same address end up sharing one location_id.
select
    printf('%05d', row_number() over (order by s.email, s.dob_date)) as user_id,
    s.gender,
    s.title,
    s.first_name,
    s.last_name,
    s.email,
    s.dob_date,
    s.dob_age,
    s.registered_date,
    s.registered_age,
    dl.location_id
from {{ ref('stg_randomuser') }} as s
join {{ ref('dim_location') }} as dl
    on s.street_number = dl.street_number
    and s.street_name = dl.street_name
    and s.city = dl.city
    and s.state = dl.state
    and s.country = dl.country
    and s.postcode = dl.postcode
