-- Fails if sleep_score (no readiness_score column in provided models) is outside 0–100.
select
  day,
  sleep_score
from {{ ref('mart_daily_wellness') }}
where sleep_score is not null
  and (sleep_score < 0 or sleep_score > 100)
