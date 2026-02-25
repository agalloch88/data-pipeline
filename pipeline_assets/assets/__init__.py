"""Dagster assets for the data pipeline."""

from dotenv import load_dotenv
load_dotenv()

from .github_activity import github_commits_data
from .oura import oura_activity_data, oura_sleep_data
from .weather import weather_daily_data

__all__ = [
    "github_commits_data",
    "oura_activity_data",
    "oura_sleep_data",
    "weather_daily_data",
]
