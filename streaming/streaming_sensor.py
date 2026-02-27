"""
Dagster sensor and asset for the real-time streaming pipeline.

The streaming_sensor polls the DuckDB streaming_events table every 30 seconds.
When new events are detected, it emits a RunRequest to trigger the streaming_summary job.
"""
from __future__ import annotations

import os
from datetime import datetime

import duckdb
from dagster import (
    RunRequest,
    SensorEvaluationContext,
    asset,
    define_asset_job,
    sensor,
)

# Default path — matches consumer.py logic
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "streaming_events.duckdb",
)
DB_PATH = os.environ.get("STREAMING_DB_PATH", DEFAULT_DB_PATH)


def _get_latest_event_id(db_path: str) -> int:
    """Return the maximum event ID in the streaming_events table, or 0 if empty."""
    try:
        con = duckdb.connect(db_path, read_only=True)
        result = con.execute("SELECT COALESCE(MAX(id), 0) FROM streaming_events").fetchone()
        con.close()
        return int(result[0]) if result else 0
    except Exception:
        return 0


@sensor(
    job=define_asset_job("streaming_summary_job", selection=["streaming_summary"]),
    minimum_interval_seconds=30,
    description="Polls DuckDB streaming_events table for new heart rate events.",
)
def streaming_events_sensor(context: SensorEvaluationContext):
    """
    Fires a RunRequest when new streaming events arrive in DuckDB.

    Cursor tracks the last processed event ID.
    """
    last_id = int(context.cursor or 0)
    current_id = _get_latest_event_id(DB_PATH)

    if current_id > last_id:
        new_count = current_id - last_id
        context.log.info(f"Detected {new_count} new streaming events (IDs {last_id + 1} to {current_id})")
        context.update_cursor(str(current_id))
        yield RunRequest(
            run_key=f"streaming-{current_id}",
            run_config={
                "ops": {
                    "streaming_summary": {
                        "config": {
                            "last_processed_id": last_id,
                            "current_id": current_id,
                        }
                    }
                }
            },
        )
    else:
        context.log.debug(f"No new events (max_id={current_id}, cursor={last_id})")


@asset(
    description="Computes rolling statistics over the last 100 streaming heart rate events.",
    group_name="streaming",
)
def streaming_summary():
    """
    Reads the most recent 100 streaming events from DuckDB and logs summary statistics.

    Stats: avg BPM, max BPM, min BPM, event count, time range.
    """
    if not os.path.exists(DB_PATH):
        print(f"STREAMING SUMMARY: Database not found at {DB_PATH}. Consumer may not have run yet.")
        return {"status": "no_data"}

    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        result = con.execute("""
            SELECT
                COUNT(*)        AS event_count,
                ROUND(AVG(bpm), 1) AS avg_bpm,
                MAX(bpm)        AS max_bpm,
                MIN(bpm)        AS min_bpm,
                MIN(timestamp)  AS earliest,
                MAX(timestamp)  AS latest
            FROM (
                SELECT * FROM streaming_events
                ORDER BY id DESC
                LIMIT 100
            )
        """).fetchone()
        con.close()

        if not result or result[0] == 0:
            print("STREAMING SUMMARY: No events in streaming_events table yet.")
            return {"status": "empty"}

        count, avg_bpm, max_bpm, min_bpm, earliest, latest = result
        summary = {
            "event_count": count,
            "avg_bpm": avg_bpm,
            "max_bpm": max_bpm,
            "min_bpm": min_bpm,
            "time_range": f"{earliest} -> {latest}",
            "computed_at": datetime.utcnow().isoformat() + "Z",
        }

        print(f"STREAMING SUMMARY (last {count} events):")
        print(f"  Avg BPM : {avg_bpm}")
        print(f"  Max BPM : {max_bpm}")
        print(f"  Min BPM : {min_bpm}")
        print(f"  Range   : {earliest} -> {latest}")

        return summary

    except Exception as exc:
        print(f"STREAMING SUMMARY: Error reading events — {exc}")
        return {"status": "error", "message": str(exc)}
