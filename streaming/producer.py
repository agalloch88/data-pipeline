#!/usr/bin/env python3
import argparse
import json
import random
import signal
import sys
import time
from datetime import datetime, timezone

from kafka import KafkaProducer


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def build_event(device_id: str) -> dict:
    bpm = int(round(random.gauss(72, 6)))
    bpm = clamp(bpm, 55, 120)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event_type": "heart_rate_sample",
        "bpm": bpm,
        "device_id": device_id,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kafka heart rate event producer")
    parser.add_argument("--broker", default="localhost:9092", help="Kafka broker host:port")
    parser.add_argument("--topic", default="health-events", help="Kafka topic name")
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Events per second (default 1.0)",
    )
    parser.add_argument(
        "--device-id",
        default="oura-1",
        help="Device identifier for emitted events",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.rate <= 0:
        print("--rate must be > 0", file=sys.stderr)
        return 2

    stop = {"flag": False}

    def handle_sigint(_signo, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        producer = KafkaProducer(
            bootstrap_servers=[args.broker],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=3,
        )
    except Exception as exc:
        print(f"Failed to initialize Kafka producer: {exc}", file=sys.stderr)
        return 1

    def on_send_error(exc: BaseException) -> None:
        print(f"Failed to send event: {exc}", file=sys.stderr)

    interval = 1.0 / args.rate
    next_time = time.monotonic()

    try:
        while not stop["flag"]:
            event = build_event(args.device_id)
            producer.send(args.topic, event).add_errback(on_send_error)

            next_time += interval
            sleep_for = next_time - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
    finally:
        try:
            producer.flush(timeout=5)
        finally:
            producer.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
