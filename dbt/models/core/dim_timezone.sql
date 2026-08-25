select distinct
    tz_offset,
    tz_description
from {{ ref('stg_randomuser') }}
