"""GitHub activity data asset."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import duckdb
import requests
from dagster import MaterializeResult, MetadataValue, asset, get_dagster_logger


@asset(description="Fetches recent GitHub PushEvent commits and stores raw JSON + DuckDB table.")
def github_commits_data() -> MaterializeResult:
    logger = get_dagster_logger()

    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")

    missing = [
        name
        for name, value in (
            ("GITHUB_TOKEN", token),
            ("GITHUB_USERNAME", username),
        )
        if not value
    ]

    if missing:
        logger.error("Missing required env vars: %s", ", ".join(missing))
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_missing_env"),
                "missing_env": MetadataValue.text(", ".join(missing)),
            }
        )

    url = f"https://api.github.com/users/{username}/events"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "data-pipeline-dagster",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        events: list[dict[str, Any]] = response.json()
    except requests.RequestException as exc:
        logger.error("GitHub Events API request failed: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )
    except ValueError as exc:
        logger.error("Failed to parse GitHub Events API response JSON: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    commits: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        repo_name = event.get("repo", {}).get("name")
        payload = event.get("payload", {})
        for commit in payload.get("commits", []) or []:
            commit_record = {
                "repo": repo_name,
                "sha": commit.get("sha"),
                "message": commit.get("message"),
                "author_name": (commit.get("author") or {}).get("name"),
                "author_email": (commit.get("author") or {}).get("email"),
                "url": commit.get("url"),
                "timestamp": event.get("created_at"),
            }
            commits.append(commit_record)

    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "raw_github_commits.json"

    try:
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(commits, handle)
    except OSError as exc:
        logger.error("Failed to write GitHub commits JSON to %s: %s", json_path, exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    db_path = data_dir / "pipeline.duckdb"
    try:
        with duckdb.connect(str(db_path)) as con:
            if not commits:
                con.execute(
                    """
                    CREATE OR REPLACE TABLE raw_github_commits (
                        repo VARCHAR, sha VARCHAR, message VARCHAR,
                        author_name VARCHAR, author_email VARCHAR,
                        url VARCHAR, timestamp VARCHAR
                    )
                    """
                )
            else:
                con.execute(
                    "create or replace table raw_github_commits as select * from read_json_auto(?)",
                    [str(json_path)],
                )
    except duckdb.Error as exc:
        logger.error("DuckDB load failed for GitHub commits: %s", exc)
        return MaterializeResult(
            metadata={
                "status": MetadataValue.text("skipped_api_error"),
                "error": MetadataValue.text(str(exc)),
            }
        )

    return MaterializeResult(
        metadata={
            "row_count": MetadataValue.int(len(commits)),
            "raw_json_path": MetadataValue.path(str(json_path)),
        }
    )
