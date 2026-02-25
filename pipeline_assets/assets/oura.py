"""Oura data assets."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import duckdb
import requests
from dagster import MaterializeResult, MetadataValue, asset, get_dagster_logger


@asset(description="Fetches last 7 days of Oura sleep data (v2) and stores raw JSON + DuckDB table.")
def oura_sleep_data() -> MaterializeResult:
    logger = get_dagster_logger()
    token = os.getenv("OURA_TOKEN")
    if not token:
        logger.error("Missing required env var: OURA_TOKEN")
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_missing_env"),
            }
        )

    today = date.today()
    start_date = today - timedelta(days=6)
    end_date = today

    url = "https://api.ouraring.com/v2/usercollection/sleep"
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except requests.RequestException as exc:
        logger.error("Oura API request failed: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )
    except ValueError as exc:
        logger.error("Failed to parse Oura API response JSON: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    records = payload.get("data", [])
    if not isinstance(records, list):
        logger.error("Unexpected Oura API response format. 'data' is not a list.")
        records = []

    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "raw_oura_sleep.json"

    try:
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(records, handle)
    except OSError as exc:
        logger.error("Failed to write Oura JSON to %s: %s", json_path, exc)
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
                "create or replace table raw_oura_sleep as select * from read_json_auto(?)",
                [str(json_path)],
            )
    except duckdb.Error as exc:
        logger.error("DuckDB load failed for Oura data: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    return MaterializeResult(
        metadata={
            "row_count": MetadataValue.int(len(records)),
            "date_range": MetadataValue.text(
                f"{start_date.isoformat()} to {end_date.isoformat()}"
            ),
            "raw_json_path": MetadataValue.path(str(json_path)),
        }
    )


@asset(
    description="Fetches last 7 days of Oura daily activity data (v2) and stores raw JSON + DuckDB table."
)
def oura_activity_data() -> MaterializeResult:
    logger = get_dagster_logger()
    token = os.getenv("OURA_TOKEN")
    if not token:
        logger.error("Missing required env var: OURA_TOKEN")
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_missing_env"),
            }
        )

    today = date.today()
    start_date = today - timedelta(days=6)
    end_date = today

    url = "https://api.ouraring.com/v2/usercollection/daily_activity"
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except requests.RequestException as exc:
        logger.error("Oura API request failed: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )
    except ValueError as exc:
        logger.error("Failed to parse Oura API response JSON: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    records = payload.get("data", [])
    if not isinstance(records, list):
        logger.error("Unexpected Oura API response format. 'data' is not a list.")
        records = []

    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "raw_oura_activity.json"

    try:
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(records, handle)
    except OSError as exc:
        logger.error("Failed to write Oura JSON to %s: %s", json_path, exc)
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
                "create or replace table raw_oura_activity as select * from read_json_auto(?)",
                [str(json_path)],
            )
    except duckdb.Error as exc:
        logger.error("DuckDB load failed for Oura data: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    return MaterializeResult(
        metadata={
            "row_count": MetadataValue.int(len(records)),
            "date_range": MetadataValue.text(
                f"{start_date.isoformat()} to {end_date.isoformat()}"
            ),
            "raw_json_path": MetadataValue.path(str(json_path)),
        }
    )
