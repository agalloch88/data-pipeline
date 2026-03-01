-- Fails if total sleep duration is outside 60–1440 minutes.
select
  id,
  day,
  total_sleep_duration
from {{ ref('stg_oura_sleep') }}
where total_sleep_duration is not null
  and (total_sleep_duration < 3600 or total_sleep_duration > 86400)
