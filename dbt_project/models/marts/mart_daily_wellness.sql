with daily_health_weather as (
  select * from {{ ref('int_daily_health_weather') }}
),
commit_counts as (
  select
    cast(committed_at as date) as day,
    count(*) as commit_count
  from {{ ref('stg_github_commits') }}
  group by 1
)
select
  daily_health_weather.day,
  daily_health_weather.sleep_score,
  daily_health_weather.sleep_hours,
  daily_health_weather.temp_f,
  daily_health_weather.humidity,
  daily_health_weather.weather_main as weather_condition,
  coalesce(commit_counts.commit_count, 0) as commit_count
from daily_health_weather
left join commit_counts
  on daily_health_weather.day = commit_counts.day
