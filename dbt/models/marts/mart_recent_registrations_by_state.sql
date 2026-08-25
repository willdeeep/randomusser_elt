with ranked as (
    select
        dl.state,
        du.user_id,
        du.first_name,
        du.last_name,
        du.registered_date,
        row_number() over (
            partition by dl.state
            order by du.registered_date desc, du.user_id
        ) as state_registration_rank
    from {{ ref('dim_user') }} as du
    join {{ ref('dim_location') }} as dl on du.location_id = dl.location_id
)

select *
from ranked
where state_registration_rank <= 3
