"""Dagster definitions for the data pipeline."""

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    in_process_executor,
    load_assets_from_modules,
)

from . import assets as assets_module

all_assets = load_assets_from_modules([assets_module])

all_assets_job = define_asset_job(
    name="daily_assets_job",
    selection=AssetSelection.all(),
    executor_def=in_process_executor,
)

daily_schedule = ScheduleDefinition(
    name="daily_assets_schedule",
    job=all_assets_job,
    cron_schedule="0 0 * * *",
)

defs = Definitions(
    assets=all_assets,
    executor=in_process_executor,
    schedules=[daily_schedule],
)
