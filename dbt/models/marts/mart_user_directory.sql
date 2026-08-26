select
    du.first_name || ' ' || du.last_name as name,
    du.gender,
    dl.city,
    dl.state,
    dl.country,
    du.email,
    {{ age_in_years('du.dob_date') }} as age,
    du.registered_date
from {{ ref('dim_user') }} as du
join {{ ref('dim_location') }} as dl on du.location_id = dl.location_id
