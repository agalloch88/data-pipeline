with daily as (
  select * from {{ ref('mart_daily_wellness') }}
)
select
  date_trunc('week', day) as week_start,
  avg(sleep_score) as avg_sleep_score,
  avg(sleep_hours) as avg_sleep_hours,
  sum(commit_count) as total_commits,
  avg(temp_f) as avg_temp_f,
  count(*) as days_tracked
from daily
group by 1
order by 1
