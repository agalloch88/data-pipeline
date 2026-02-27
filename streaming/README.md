# Real-Time Streaming Pipeline

A Kafka-based streaming component that extends the batch Health and Activity Analytics pipeline with real-time event ingestion and processing.

## Architecture

```
Kafka Producer -> Kafka Broker -> Consumer -> DuckDB -> Dagster Sensor -> Summary Asset
```

## Quick Start

1. `cd streaming && docker-compose up -d`
2. `python streaming/consumer.py`
3. `python streaming/producer.py`
4. `Watch events flow into DuckDB in real-time`
5. `duckdb data/streaming_events.duckdb -c "SELECT COUNT(*), AVG(bpm) FROM streaming_events"`

## Integration with Dagster

Run `dagster dev` from the project root, then open `http://localhost:3000`. Enable the `streaming_events_sensor` under Automation and materialize `streaming_summary` under Assets.

## Configuration

```bash
python streaming/producer.py --broker localhost:9092 --topic health-events --rate 2.0
python streaming/consumer.py --broker localhost:9092 --topic health-events --db-path data/streaming_events.duckdb
```

```bash
DUCKDB_PATH=/path/to/custom.duckdb
```

## Event Schema

```json
{
  "timestamp": "2026-02-27T09:00:00.123Z",
  "event_type": "heart_rate_sample",
  "bpm": 72,
  "device_id": "oura-1"
}
```

```sql
CREATE TABLE streaming_events (
    id          BIGINT,
    timestamp   TIMESTAMPTZ,
    event_type  VARCHAR,
    bpm         INTEGER,
    device_id   VARCHAR,
    ingested_at TIMESTAMPTZ
);
```

## Design Decisions

Kafka provides durable, replayable event storage with consumer group semantics. If the consumer goes down, it can resume from its last committed offset without losing events. This is the standard for high-volume streaming in production DE environments.

DuckDB is the existing analytical store for this project. Using it as the streaming sink demonstrates the same database handling both batch (via dbt medallion models) and streaming (via direct writes), which is a common lakehouse pattern for smaller-scale analytics workloads where a dedicated streaming store would add operational overhead without benefit.

The consumer group design uses a single consumer group named `health-analytics` with one consumer. For horizontal scaling, multiple consumers in the same group would each process a subset of partitions. The current topic uses 1 partition, so only one consumer is active at a time.

Event generation uses a normal distribution (mean 72 bpm, std 6, clipped 55 to 120) to simulate realistic resting heart rate variation. This is not real Oura data but demonstrates the streaming pattern with realistic-looking data.

## Stopping

```bash
docker compose -f streaming/docker-compose.yml down
```
