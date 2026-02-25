-- source: main.raw_oura_sleep
select
  id,
  cast(day as date) as day,
  try_cast(total_sleep_duration as double) as total_sleep_duration,
  try_cast(rem_sleep_duration as double) as rem_sleep_duration,
  try_cast(deep_sleep_duration as double) as deep_sleep_duration,
  try_cast(efficiency as double) as efficiency,
  try_cast(lowest_heart_rate as double) as hr_lowest,
  try_cast(average_heart_rate as double) as hr_average
from main.raw_oura_sleep
