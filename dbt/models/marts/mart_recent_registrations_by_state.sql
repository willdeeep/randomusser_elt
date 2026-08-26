with ranked as (
    select
        du.first_name || ' ' || du.last_name as name,
        du.gender,
        dl.city,
        dl.state,
        dl.country,
        du.email,
        {{ age_in_years('du.dob_date') }} as age,
        du.registered_date,
        row_number() over (
            partition by dl.state
            order by du.registered_date desc, du.user_id
        ) as state_registration_rank
    from {{ ref('dim_user') }} as du
    join {{ ref('dim_location') }} as dl on du.location_id = dl.location_id
    -- "state" here means US state; filtering to US rows before ranking so a UK county
    -- of the same name (if the seed ever produced one) couldn't be ranked alongside it.
    where dl.country = 'United States'
)

select
    name,
    gender,
    city,
    state,
    country,
    email,
    age,
    registered_date
from ranked
where state_registration_rank <= 3
