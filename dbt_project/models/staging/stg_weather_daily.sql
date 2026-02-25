-- source: main.raw_weather_daily
select
  to_timestamp(try_cast(dt as bigint)) as dt,
  try_cast(main.temp as double) as temp_kelvin,
  try_cast(main.feels_like as double) as feels_like_kelvin,
  try_cast(main.humidity as double) as humidity,
  try_cast(main.pressure as double) as pressure,
  try_cast(wind.speed as double) as wind_speed,
  weather[1].main as weather_main,
  weather[1].description as weather_description,
  try_cast(clouds.all as double) as clouds_all,
  (
    (try_cast(main.temp as double) - 273.15) * 9.0 / 5.0 + 32.0
  ) as temp_f
from main.raw_weather_daily
