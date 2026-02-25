#!/usr/bin/env bash
set -euo pipefail

# Load API tokens from secrets
export OURA_TOKEN="$(cat ~/.openclaw/.secrets/oura-token)"
export GITHUB_TOKEN="$(cat ~/.openclaw/.secrets/github-classic-pat)"
export GITHUB_USERNAME="youvereachedhenryjones"
export WEATHER_LAT="35.2271"
export WEATHER_LON="-80.8431"

# OpenWeatherMap is optional
if [ -f ~/.openclaw/.secrets/openweathermap-key ] && [ -s ~/.openclaw/.secrets/openweathermap-key ]; then
    export OPENWEATHERMAP_KEY="$(cat ~/.openclaw/.secrets/openweathermap-key)"
    echo "✅ OpenWeatherMap key loaded"
else
    echo "⚠️  No OpenWeatherMap key found — weather asset will skip"
fi

cd "$(dirname "$0")/.."

echo "🚀 Materializing Dagster assets..."
python -c "
from pipeline_assets.assets import github_commits_data, oura_sleep_data, oura_activity_data, weather_daily_data
from dagster import materialize

result = materialize([github_commits_data, oura_sleep_data, oura_activity_data, weather_daily_data])
print('Asset materialization result:', result.success)
"
