# Real-Time Streaming Pipeline

A Kafka-based streaming component that extends the batch Health and Activity Analytics pipeline with real-time event ingestion and processing.

## Architecture

```
┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Event Producer  │    │  Apache Kafka   │    │  Event Consumer │
├──────────────────┤    ├─────────────────┤    ├─────────────────┤
│ producer.py      │───▶│ health-events   │───▶│ consumer.py     │
│ Synthetic BPM    │    │ topic           │    │ Kafka → DuckDB  │
│ (55-120 bpm)     │    │ (1 partition)   │    │ streaming_events│
└──────────────────┘    └─────────────────┘    └────────┬────────┘
                                                         │
                        ┌─────────────────┐              │ new events?
                        │ Dagster Sensor  │◀─────────────┘
                        │ (every 30s)     │
                        └────────┬────────┘
                                 │ RunRequest
                        ┌────────▼────────┐
                        │ streaming_      │
                        │ summary asset   │
                        │ avg/max/min BPM │
                        └─────────────────┘
```

**Data flow:** Producer generates synthetic heart rate events at configurable rate → Kafka broker holds events in topic → Consumer reads and writes to DuckDB `streaming_events` table → Dagster sensor detects new events → `streaming_summary` asset computes rolling statistics.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Kafka + Zookeeper local environment |
| `producer.py` | Synthetic heart rate event generator |
| `consumer.py` | Kafka consumer that writes to DuckDB |
| `streaming_sensor.py` | Dagster sensor + summary asset |

## Quick Start

### Prerequisites
```bash
# Docker Desktop running (for Kafka)
# Python dependencies installed
pip install kafka-python duckdb dagster
```

### Step 1: Start Kafka
```bash
cd streaming
docker-compose up -d
# Verify: docker-compose ps
```

### Step 2: Start the Consumer
In a separate terminal:
```bash
python streaming/consumer.py
# Connects to localhost:9092, reads health-events topic
# Writes to data/streaming_events.duckdb
```

### Step 3: Start the Producer
In another terminal:
```bash
python streaming/producer.py
# Generates ~1 event/second
# You should see consumer output immediately
```

### Step 4: Verify Data in DuckDB
```bash
duckdb data/streaming_events.duckdb -c "SELECT COUNT(*), ROUND(AVG(bpm),1) as avg_bpm, MAX(bpm), MIN(bpm) FROM streaming_events"
```

### Step 5: (Optional) Dagster Integration
```bash
# From the project root:
dagster dev
# Navigate to localhost:3000
# Find the streaming_events_sensor under Automation
# Find streaming_summary under Assets
```

## Configuration

### Producer Args
```bash
python streaming/producer.py \
  --broker localhost:9092 \
  --topic health-events \
  --rate 2.0          # events per second (default: 1.0)
```

### Consumer Args
```bash
python streaming/consumer.py \
  --broker localhost:9092 \
  --topic health-events \
  --db-path data/streaming_events.duckdb
```

### Environment Variables
```bash
STREAMING_DB_PATH=/path/to/custom.duckdb  # Override DuckDB path for Dagster sensor
```

## Event Schema

Each event published to Kafka:
```json
{
  "timestamp": "2026-02-27T09:00:00.123Z",
  "event_type": "heart_rate_sample",
  "bpm": 72,
  "device_id": "oura-1"
}
```

DuckDB `streaming_events` table:
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

**Why Kafka:** Kafka provides durable, replayable event storage with consumer group semantics. Even if the consumer goes down, it can resume from its last committed offset without losing events. This is the standard for high-volume streaming in production DE environments.

**Why DuckDB as the streaming sink:** DuckDB is the existing analytical store for this project (batch pipeline). Using it as the streaming sink demonstrates the same database handling both batch (via dbt medallion models) and streaming (via direct writes), which is a common "lakehouse" pattern for smaller-scale analytics workloads where a dedicated streaming store (Cassandra, Redis) would add operational overhead without benefit.

**Consumer group design:** Using a single consumer group (`health-analytics`) with one consumer. For horizontal scaling, multiple consumers in the same group would each process a subset of partitions. The current topic uses 1 partition, so only one consumer is active at a time.

**Event generation:** The producer uses a normal distribution (mean=72 bpm, std=6, clipped 55-120) to simulate realistic resting heart rate variation. This is not real Oura data but demonstrates the streaming pattern with realistic-looking data.

## Stopping

```bash
# Stop producer/consumer: Ctrl+C in each terminal
# Stop Kafka:
docker-compose down
```

---

*Part of the Multi-Source Health and Activity Analytics Pipeline | See root README for the full batch pipeline.*
