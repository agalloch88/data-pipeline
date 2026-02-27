# Architecture Decision Records

This document captures the architectural decisions made during the design and build of the Multi-Source Health and Activity Analytics Pipeline. Each record explains the problem context, the decision made, the alternatives considered, and the tradeoffs accepted.

These are written for two audiences: future maintainers of this project, and anyone evaluating this codebase as a portfolio piece. Where a decision would differ in a production environment, that context is noted explicitly.

---

## ADR Index

| ID | Title | Status |
|----|-------|--------|
| [ADR-001](#adr-001-duckdb-as-the-analytical-store) | DuckDB as the Analytical Store | Accepted |
| [ADR-002](#adr-002-dagster-over-airflow-for-orchestration) | Dagster over Airflow for Orchestration | Accepted |
| [ADR-003](#adr-003-dbt-core-over-dbt-cloud) | dbt Core over dbt Cloud | Accepted |
| [ADR-004](#adr-004-medallion-architecture-for-data-modeling) | Medallion Architecture for Data Modeling | Accepted |
| [ADR-005](#adr-005-kafka-streaming-component) | Kafka Streaming Component | Accepted |

---

## ADR-001: DuckDB as the Analytical Store

**Status:** Accepted

### Context

The pipeline processes health metrics, GitHub activity, and weather data to produce analytical marts. The workload is read-heavy and analytical: aggregations over time-series data, multi-table joins, column-oriented scans. The project is local-first and solo-developer, with no multi-user concurrency requirement. Cost is a real constraint for a portfolio project.

### Decision

Use DuckDB as the primary data warehouse.

DuckDB is an embedded, in-process OLAP database with no server to provision or manage. It reads and writes Parquet natively, runs columnar scans efficiently, and supports the full SQL standard including window functions and complex aggregations. For this workload and this scale, it is the right tool.

### Alternatives Considered

**Snowflake.** The production standard for cloud data warehousing. Excellent for multi-user concurrency, near-unlimited scale, and enterprise feature sets. Rejected because a portfolio project does not need a $500/month warehouse. The skills signal here is knowing *when* Snowflake is worth its cost, not running it for 50MB of personal health data.

**BigQuery.** Strong managed OLAP with serverless pricing. Adds GCP vendor dependency, requires cloud credentials in CI, and introduces network latency for every query. The free tier is viable but constraining. Rejected for the same reason as Snowflake: the operational overhead does not match the project scale.

**PostgreSQL.** A relational OLTP database, not an OLAP one. PostgreSQL can handle analytical queries, but it is row-oriented and not optimized for the column-scan patterns that dominate this workload. Using PostgreSQL here would demonstrate a category mismatch between workload and tool.

**SQLite.** Embedded and zero-cost like DuckDB, but row-oriented and missing many analytical SQL features. Not designed for this use case.

### Consequences

Accepted tradeoffs:
- No cloud experience signal from this project alone. A senior engineer reviewing this codebase should read this ADR and understand the decision was deliberate, not a gap.
- No multi-user concurrency. DuckDB supports one writer at a time. This is fine for a single-developer pipeline; it would be a hard constraint at team scale.
- No managed infrastructure. All data lives on local disk. Backup and durability are the developer's responsibility.

Benefits gained:
- Zero cost, zero cloud dependencies, instant local iteration.
- Full SQL support with window functions, lateral joins, and efficient columnar scans.
- Tight integration with dbt and Python. DuckDB's Python API makes ad-hoc analysis trivial alongside the pipeline.
- Demonstrates understanding of OLAP vs. OLTP distinctions, which is the actual skill being signaled.

---

## ADR-002: Dagster over Airflow for Orchestration

**Status:** Accepted

### Context

The pipeline needs an orchestrator to schedule and coordinate extract, load, and transform steps across three data sources. The orchestrator should handle dependency management, provide observability, and model the pipeline in a way that reflects how data engineering actually works: data assets with lineage, not task graphs with execution order.

### Decision

Use Dagster with asset-centric definitions.

Dagster's Software-Defined Assets model fits this pipeline directly. Each stage of the pipeline is an asset: raw API responses, staging tables, intermediate joins, final marts. Dagster tracks which assets are materialized, when they were last updated, and what downstream assets depend on them. Data lineage is built in, not bolted on. The type system catches schema mismatches before they reach downstream consumers.

### Alternatives Considered

**Apache Airflow.** The dominant orchestrator in the industry. Airflow has a massive ecosystem, widespread adoption, and deep integrations with every major cloud platform. It is also DAG-centric and imperative: you define tasks and their execution order, and you wire up dependencies manually. Data lineage requires plugins or external tooling. For a pipeline that is fundamentally about data assets, Airflow's mental model works against the grain. It was rejected here because Dagster's asset model more accurately represents the problem being solved.

One practical note: Airflow is more frequently listed in job postings. Choosing Dagster is a deliberate bet on the direction the industry is moving, not ignorance of Airflow's prevalence.

**Prefect.** Modern, developer-friendly, and Python-native. Prefect's flow and task model is closer to Airflow than Dagster in its core abstraction. It has a strong cloud product but a smaller open-source ecosystem than either Airflow or Dagster. Rejected because Dagster's data-aware abstractions are a better fit for an analytically-focused portfolio project.

**cron + Python scripts.** Viable for simple pipelines. Does not provide dependency management, observability, retry logic, or any of the operational scaffolding that makes a pipeline maintainable at scale. Ruled out because the goal is demonstrating engineering judgment, not minimizing tooling.

### Consequences

Accepted tradeoffs:
- Dagster has a smaller job market footprint than Airflow. This is a real cost. Engineers who know only Dagster will find fewer postings that list it by name.
- Dagster's asset model has a learning curve if you are coming from a task-centric mental model.

Benefits gained:
- Assets are the right abstraction for data pipelines. The code reads like what it does.
- Built-in data lineage graph, observable in the Dagster UI without any additional tooling.
- Type annotations on assets catch integration errors at definition time, not execution time.
- The `@sensor` primitive integrates cleanly with the streaming component (see ADR-005).

---

## ADR-003: dbt Core over dbt Cloud

**Status:** Accepted

### Context

The transform layer requires a framework that supports SQL-based transformations, automated testing, documentation generation, and version control. The project uses a three-layer medallion model with 7 models and 17 data quality tests.

### Decision

Use dbt Core, self-managed, executed via Dagster.

dbt Core is the open-source foundation of dbt. It handles model compilation, dependency resolution, incremental processing, and the full test suite. Running it via Dagster's `@asset` definitions means transformations are first-class citizens in the orchestration graph, with lineage tracked alongside extraction and loading steps.

### Alternatives Considered

**dbt Cloud.** The managed platform built on top of dbt Core. Adds a hosted scheduler, managed CI/CD, a browser-based IDE, and SSO. These are real features with real value on engineering teams. Rejected for three reasons: cost (free tier is limited), redundancy (Dagster already handles scheduling and orchestration), and the goal of demonstrating hands-on understanding of the transformation layer rather than delegating it to a managed service.

A senior engineer using dbt Cloud at work understands the scheduler, the CI/CD hooks, and the run history. A senior engineer who has operated dbt Core self-managed also understands what dbt Cloud is abstracting for you. This project targets the latter signal.

**Custom SQL scripts.** Rejected outright. No testing framework, no dependency management, no documentation, no incremental model support. Custom SQL scripts would require reinventing everything dbt Core provides.

**SQLMesh.** An emerging alternative with state-aware migrations and a different approach to incremental models. Interesting, but the ecosystem is smaller and the dbt skill signal is more immediately legible to engineering teams.

### Consequences

Accepted tradeoffs:
- No managed CI/CD. Running `dbt test` in GitHub Actions requires manual configuration.
- No hosted scheduler. Dagster handles this, which works well but creates a tighter coupling between the orchestrator and the transformation layer.

Benefits gained:
- Full control over the transformation environment, including package management and profile configuration.
- Git-native workflow: models, tests, and documentation live in the repository alongside the rest of the pipeline code.
- Deep understanding of dbt internals: compiled SQL, the ref() dependency system, the test YAML schema, incremental strategies. These are visible in this codebase in ways they would not be in a managed environment.

---

## ADR-004: Medallion Architecture for Data Modeling

**Status:** Accepted

### Context

The pipeline ingests raw JSON from three APIs with different schemas, update frequencies, and quality characteristics. The data needs to be cleaned, joined, and aggregated to produce analytical marts. The modeling pattern should support testing at each stage and make it easy to debug problems by inspecting intermediate state.

### Decision

Use a three-layer medallion architecture: Staging, Intermediate, and Marts.

**Staging** models are 1:1 with source tables. They rename columns, cast types, and apply no business logic. A staging model is a clean, typed representation of the source, nothing more.

**Intermediate** models join and enrich data across sources. The `int_daily_health_weather` model joins sleep metrics, activity data, and weather conditions on the date grain. Joins happen here so they can be tested here.

**Marts** are business-facing aggregations. `mart_daily_wellness` and `mart_weekly_summary` are the outputs that the Streamlit dashboard queries. Marts have the strongest test coverage because they are the layer that end consumers depend on.

This layering means any failure can be localized to a specific stage. A bad join lives in Intermediate. A bad aggregation lives in Marts. Bad source data fails at Staging before it can propagate.

### Alternatives Considered

**Star schema applied directly to raw data.** A dimensional model with fact and dimension tables is a valid pattern for analytical workloads. Rejected here because it assumes cleaner source data than APIs provide. The staging layer exists precisely to normalize API responses before they enter a formal schema.

**One Big Table (OBT).** Denormalized, wide, fast to query. Works well for a narrow set of queries but breaks down as the question set grows. Adding a new join or a new grain means rebuilding the OBT. No separation of concerns, no intermediate testability. Rejected.

**Ad-hoc CTEs in the mart layer.** Pulling raw data directly into mart models via CTEs without a staging layer. This works in small projects but makes the transformation logic impossible to test at intermediate stages. Debugging a mart failure requires tracing back through all the CTEs. Rejected because testability at each layer is a design requirement.

### Consequences

Accepted tradeoffs:
- More models to maintain. Seven models for two marts is more than the minimum, but each model is simple and independently testable.
- Intermediate state stored in the database. More disk usage, but invaluable for debugging.

Benefits gained:
- Each layer is independently testable. The 17-test suite is distributed across staging (8 tests), intermediate (3 tests), and marts (6 tests).
- Schema changes in source APIs fail at the staging layer, not in the mart. This is the design intent of the staging abstraction.
- The model structure is immediately legible to any data engineer familiar with medallion architecture. The pattern is a communication tool as much as a technical one.

---

## ADR-005: Kafka Streaming Component

**Status:** Accepted

### Context

The batch pipeline demonstrates ELT, orchestration, data modeling, and testing. It does not demonstrate real-time event processing. Stream processing is a distinct skill set with distinct tooling, and the absence of any streaming component would be a visible gap for roles that involve real-time data.

The decision was to extend the portfolio with a streaming mini-project that integrates with the existing batch infrastructure rather than building a separate standalone project.

### Decision

Add a Kafka-based streaming pipeline alongside the batch pipeline, sharing the DuckDB store and the Dagster orchestration layer.

The architecture:

```
Producer (synthetic heart rate events)
  -> Kafka broker (Docker Compose)
    -> Consumer (writes to DuckDB)
      -> Dagster sensor (monitors event count)
        -> streaming_summary asset (materialized on threshold)
```

The producer generates synthetic `heart_rate_sample` events using a normal distribution (mean 72 bpm, std 6, clipped 55 to 120) at a configurable rate. The consumer uses consumer group semantics, committing offsets after each write so it can resume without data loss after a restart. The Dagster sensor polls the event count in DuckDB and materializes the `streaming_summary` asset when the threshold is met.

Using DuckDB as the streaming sink is a deliberate design choice. It demonstrates the lakehouse pattern: one analytical store handling both batch and streaming writes. In production, you might separate these concerns with a dedicated streaming store. At this scale, keeping a single store reduces operational complexity and makes the integration more legible.

### Alternatives Considered

**Flink.** The production standard for stateful stream processing. Rich API, exactly-once semantics, complex event processing. Rejected because the scope here is demonstrating streaming ingestion and integration, not stateful stream processing. Flink would be the right tool for windowed aggregations over high-volume streams.

**Spark Structured Streaming.** Strong for micro-batch processing with Spark compatibility. Heavier operationally than Kafka plus a lightweight consumer. Rejected for the same reason as Flink: the goal is integration, not volume.

**Redis Streams.** Lightweight and fast. Smaller ecosystem and less commonly cited in data engineering roles than Kafka. Rejected because Kafka is the dominant streaming platform in production DE environments, and this project should signal familiarity with it.

**A separate standalone streaming project.** Keeping the streaming work isolated from the batch pipeline would mean duplicating infrastructure and losing the integration story. The Dagster sensor connecting the streaming events to a materialized asset is the interesting part. That connection only exists because the two components share a platform.

### Consequences

Accepted tradeoffs:
- Docker Compose dependency. Running the streaming component requires a local Docker installation for the Kafka broker.
- Single-partition topic. The current configuration supports one active consumer. Horizontal scaling would require adding partitions and consumer instances, which is straightforward but not demonstrated here.
- Synthetic data. The producer generates simulated heart rate events. The streaming component demonstrates the pattern, not a live data source.

Benefits gained:
- The portfolio now demonstrates both batch and streaming competencies in a single cohesive project.
- Kafka consumer group semantics, offset management, and at-least-once delivery are all demonstrated in the consumer implementation.
- The Dagster sensor integration shows how to bridge a streaming component into an asset-centric orchestration model, which is a real architectural problem in production pipelines.
- The DuckDB-as-streaming-sink pattern demonstrates the lakehouse architecture: one analytical store, two ingestion paths.

---

*Last updated: 2026-02-27*
*Author: Ryan Kirsch*
