with sleep as (
  select
    *,
    row_number() over (
      partition by day
      order by total_sleep_duration desc
    ) as rn
  from {{ ref('stg_oura_sleep') }}
),
sleep_daily as (
  select *
  from sleep
  where rn = 1
),
weather as (
  select * from {{ ref('stg_weather_daily') }}
)
select
  sleep_daily.day as day,
  sleep_daily.efficiency as sleep_score,
  sleep_daily.total_sleep_duration / 3600.0 as sleep_hours,
  weather.temp_f,
  weather.humidity,
  weather.weather_main
from sleep_daily
left join weather
  on sleep_daily.day = cast(weather.dt as date)
