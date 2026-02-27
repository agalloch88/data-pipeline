#!/usr/bin/env python3
import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import duckdb
from kafka import KafkaConsumer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kafka heart rate event consumer")
    parser.add_argument("--broker", default="localhost:9092", help="Kafka broker host:port")
    parser.add_argument("--topic", default="health-events", help="Kafka topic name")
    parser.add_argument(
        "--db-path",
        default=None,
        help="DuckDB path (default data/streaming_events.duckdb)",
    )
    return parser.parse_args()


def resolve_db_path(arg_path: Optional[str]) -> str:
    if arg_path:
        return arg_path
    preferred = os.path.join("data", "health_analytics.duckdb")
    if os.path.exists(preferred):
        return preferred
    return os.path.join("data", "streaming_events.duckdb")


def ensure_table(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS streaming_events (
            id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            timestamp TIMESTAMPTZ,
            event_type VARCHAR,
            bpm INTEGER,
            device_id VARCHAR,
            ingested_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )


def get_lag(consumer: KafkaConsumer) -> int:
    partitions = consumer.assignment()
    if not partitions:
        return 0
    end_offsets = consumer.end_offsets(partitions)
    lag = 0
    for tp in partitions:
        position = consumer.position(tp)
        end = end_offsets.get(tp, position)
        if end is not None and position is not None:
            lag += max(0, end - position)
    return lag


def main() -> int:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)

    stop = {"flag": False}

    def handle_sigint(_signo, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, handle_sigint)

    def safe_deserializer(value: Optional[bytes]) -> Optional[dict]:
        if value is None:
            return None
        try:
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"Skipping malformed message: {exc}", file=sys.stderr)
            return None

    try:
        consumer = KafkaConsumer(
            args.topic,
            bootstrap_servers=[args.broker],
            group_id="health-analytics",
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            value_deserializer=safe_deserializer,
        )
    except Exception as exc:
        print(f"Failed to initialize Kafka consumer: {exc}", file=sys.stderr)
        return 1

    conn = duckdb.connect(db_path)
    ensure_table(conn)

    consumed_total = 0
    since_commit = 0
    last_commit_time = time.monotonic()
    last_stats_time = time.monotonic()
    last_bpm = 0

    try:
        while not stop["flag"]:
            records = consumer.poll(timeout_ms=1000)
            for _tp, messages in records.items():
                for message in messages:
                    event = message.value
                    if event is None:
                        continue
                    try:
                        conn.execute(
                            """
                            INSERT INTO streaming_events (timestamp, event_type, bpm, device_id)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                event.get("timestamp"),
                                event.get("event_type"),
                                event.get("bpm"),
                                event.get("device_id"),
                            ),
                        )
                    except Exception as exc:
                        print(f"DuckDB insert failed: {exc}", file=sys.stderr)
                        continue
                    consumed_total += 1
                    since_commit += 1
                    if event.get("bpm") is not None:
                        last_bpm = event.get("bpm")

                    now = time.monotonic()
                    if since_commit >= 10 or (now - last_commit_time) >= 5:
                        consumer.commit()
                        last_commit_time = now
                        since_commit = 0

            now = time.monotonic()
            if since_commit > 0 and (now - last_commit_time) >= 5:
                consumer.commit()
                last_commit_time = now
                since_commit = 0

            if (now - last_stats_time) >= 30:
                lag = get_lag(consumer)
                stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
                print(
                    f"[{stamp}] Consumed: {consumed_total} events | Lag: {lag} | Last BPM: {last_bpm}"
                )
                last_stats_time = now
    finally:
        try:
            if since_commit > 0:
                consumer.commit()
        finally:
            try:
                consumer.close()
            finally:
                conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
