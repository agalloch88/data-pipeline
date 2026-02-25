"""OpenWeatherMap daily weather data asset."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import duckdb
import requests
from dagster import MaterializeResult, MetadataValue, asset, get_dagster_logger


@asset(description="Fetches current weather from OpenWeatherMap and stores raw JSON + DuckDB table.")
def weather_daily_data() -> MaterializeResult:
    logger = get_dagster_logger()

    api_key = os.getenv("OPENWEATHERMAP_KEY")

    if not api_key or api_key.strip().lower() in {"skip", "none"}:
        logger.warning("OPENWEATHERMAP_KEY is set to skip — weather data will be empty")
        project_root = Path(__file__).resolve().parents[2]
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        json_path = data_dir / "raw_weather.json"

        try:
            with json_path.open("w", encoding="utf-8") as handle:
                json.dump([], handle)
        except OSError as exc:
            logger.error("Failed to write weather JSON to %s: %s", json_path, exc)
            return MaterializeResult(
                metadata={
                    "status": MetadataValue.text("skipped_api_error"),
                    "error": MetadataValue.text(str(exc)),
                }
            )

        db_path = data_dir / "pipeline.duckdb"
        try:
            with duckdb.connect(str(db_path)) as con:
                con.execute(
                    """
                    CREATE OR REPLACE TABLE raw_weather_daily (
                        dt BIGINT,
                        main JSON,
                        wind JSON,
                        weather JSON,
                        clouds JSON
                    )
                    """
                )
        except duckdb.Error as exc:
            logger.error("DuckDB load failed for empty weather data: %s", exc)
            return MaterializeResult(
                metadata={
                    "status": MetadataValue.text("skipped_api_error"),
                    "error": MetadataValue.text(str(exc)),
                }
            )

        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_no_api_key"),
                "raw_json_path": MetadataValue.path(str(json_path)),
            }
        )

    lat = os.getenv("WEATHER_LAT")
    lon = os.getenv("WEATHER_LON")

    if not lat or not lon:
        logger.error("Missing required env vars: WEATHER_LAT, WEATHER_LON")
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_missing_env"),
                "missing_env": MetadataValue.text("WEATHER_LAT, WEATHER_LON"),
            }
        )

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except requests.RequestException as exc:
        logger.error("OpenWeatherMap request failed: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )
    except ValueError as exc:
        logger.error("Failed to parse OpenWeatherMap response JSON: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "raw_weather.json"

    try:
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump([payload], handle)
    except OSError as exc:
        logger.error("Failed to write weather JSON to %s: %s", json_path, exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    db_path = data_dir / "pipeline.duckdb"
    try:
        with duckdb.connect(str(db_path)) as con:
            con.execute(
                "create or replace table raw_weather_daily as select * from read_json_auto(?)",
                [str(json_path)],
            )
    except duckdb.Error as exc:
        logger.error("DuckDB load failed for weather data: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    return MaterializeResult(
        metadata={
            "row_count": MetadataValue.int(1),
            "raw_json_path": MetadataValue.path(str(json_path)),
        }
    )
