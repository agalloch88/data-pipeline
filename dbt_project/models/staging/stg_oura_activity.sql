-- source: main.raw_oura_activity
select
  id,
  cast(day as date) as day,
  try_cast(score as int) as activity_score,
  try_cast(active_calories as int) as active_calories,
  try_cast(total_calories as int) as total_calories,
  try_cast(steps as int) as steps,
  try_cast(equivalent_walking_distance as int) as equivalent_walking_distance,
  try_cast(sedentary_time as int) as sedentary_time
from main.raw_oura_activity
