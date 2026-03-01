-- Fails if there are gaps in the day spine in the daily mart.
with ordered as (
  select
    day,
    lag(day) over (order by day) as prev_day
  from {{ ref('mart_daily_wellness') }}
)
select
  day,
  prev_day
from ordered
where prev_day is not null
  and day <> prev_day + interval '1 day'
