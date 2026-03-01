-- Fails if activity_score is outside 0–100.
select
  id,
  day,
  activity_score
from {{ ref('stg_oura_activity') }}
where activity_score is not null
  and (activity_score < 0 or activity_score > 100)
