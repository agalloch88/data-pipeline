# Multi-Source Health and Activity Analytics Pipeline

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Dagster](https://img.shields.io/badge/Dagster-1.x-orange.svg)](https://dagster.io)
[![dbt](https://img.shields.io/badge/dbt-Core-red.svg)](https://getdbt.com)
[![DuckDB](https://img.shields.io/badge/DuckDB-OLAP-yellow.svg)](https://duckdb.org)
[![Tests](https://img.shields.io/badge/dbt%20tests-17%20passing-green.svg)]()

A production-ready ELT pipeline that correlates personal health metrics, coding activity, and environmental data to derive actionable wellness insights. Built with modern data engineering practices including asset-centric orchestration, medallion architecture, and comprehensive data quality testing.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Orchestration  │    │   Transform     │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ Oura Ring v2    │───▶│ Dagster Assets   │───▶│ dbt Core        │
│ GitHub Events   │    │ (Extract/Load)   │    │ (Medallion)     │
│ OpenWeatherMap  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│  Visualization  │    │   Data Warehouse │             │
├─────────────────┤    ├──────────────────┤             │
│ Streamlit       │◀───│ DuckDB (OLAP)    │◀────────────┘
│ Dashboard       │    │ Analytical Store │
└─────────────────┘    └──────────────────┘

Data Flow: API → Raw JSON → Staging → Intermediate → Data Marts → Analytics
```

## What This Demonstrates

**Core Data Engineering Competencies:**
- **ELT Pipeline Design**: Modern extract-load-transform pattern with clear separation of concerns
- **Data Orchestration**: Asset-centric approach using Dagster for dependency management and data lineage
- **Data Modeling**: Medallion architecture (staging → intermediate → marts) following dimensional modeling principles
- **Data Quality**: Comprehensive test suite with 17 dbt tests covering completeness, uniqueness, and referential integrity
- **Database Selection**: DuckDB for OLAP workloads, demonstrating understanding of analytical vs transactional systems
- **Real-World Application**: Production-grade pipeline processing actual personal data, not synthetic datasets

**Technical Architecture:**
- **Declarative Transformations**: SQL-based transformations with dbt for maintainability and version control
- **Data Lineage**: Full traceability from source APIs through final analytics marts
- **Incremental Processing**: Efficient data updates using dbt's incremental models
- **Schema Evolution**: Robust handling of API schema changes through staging layer abstraction

## Tech Stack

- **Orchestration**: Dagster (asset-centric data pipelines)
- **Transformation**: dbt Core (SQL-based ELT with testing framework)
- **Warehouse**: DuckDB (columnar analytical database)
- **Runtime**: Python 3.13
- **Visualization**: Streamlit (interactive dashboard)
- **Data Sources**: Oura Ring API v2, GitHub Events API, OpenWeatherMap API

## Data Model

### Staging Layer
```sql
stg_oura_sleep          -- Raw sleep metrics (duration, efficiency, REM/deep phases)
stg_oura_activity       -- Daily activity summaries (steps, calories, active minutes)  
stg_weather_daily       -- Environmental conditions (temperature, humidity, pressure)
stg_github_commits      -- Development activity (commit frequency, timing patterns)
```

### Intermediate Layer
```sql
int_daily_health_weather -- Joined health metrics with weather context
```

### Data Marts
```sql
mart_daily_wellness     -- Comprehensive daily health and activity scores
mart_weekly_summary     -- Aggregated weekly trends and correlations
```

## Key Features

**Data Integration:**
- Real-time health metrics from Oura Ring (sleep quality, readiness scores, activity levels)
- Development activity patterns from GitHub Events API
- Environmental correlation via OpenWeatherMap integration

**Analytics Capabilities:**
- Cross-domain correlation analysis (sleep quality vs coding productivity)
- Weather impact on physical activity and recovery metrics
- Temporal pattern recognition in health and work habits
- Weekly trend analysis with statistical significance testing

**Data Quality Assurance:**
- 17 automated data quality tests covering completeness, uniqueness, and referential integrity
- Schema validation for all API inputs
- Null handling and data type enforcement
- Historical consistency checks

## Setup Instructions

### Prerequisites
- Python 3.13+
- Personal Oura Ring account with API access
- GitHub personal access token
- OpenWeatherMap API key (optional)

### Installation

1. **Clone and setup environment:**
   ```bash
   git clone https://github.com/youvereachedhenryjones/data-pipeline.git
   cd data-pipeline
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials:
   # OURA_ACCESS_TOKEN=your_oura_token
   # GITHUB_TOKEN=your_github_token  
   # OPENWEATHER_API_KEY=your_weather_key
   ```

3. **Initialize database and run dbt models:**
   ```bash
   # Initialize DuckDB and create schemas
   python scripts/init_db.py
   
   # Run dbt transformations
   cd dbt_transform
   dbt deps
   dbt run
   dbt test
   ```

4. **Start Dagster orchestration:**
   ```bash
   dagster dev
   # Access UI at http://localhost:3000
   ```

5. **Launch Streamlit dashboard:**
   ```bash
   streamlit run streamlit_app.py
   # Access dashboard at http://localhost:8501
   ```

## Pipeline Execution

The pipeline runs on a configurable schedule with the following stages:

1. **Extract**: Dagster assets fetch data from APIs with error handling and rate limiting
2. **Load**: Raw JSON stored in DuckDB with metadata tracking
3. **Transform**: dbt models process data through medallion architecture layers
4. **Quality**: Automated testing validates data integrity and business rules
5. **Serve**: Analytical marts power Streamlit dashboard and ad-hoc queries

## Data Quality and Testing

All transformations include comprehensive testing:
- **Completeness tests**: Ensure required fields are populated
- **Uniqueness tests**: Prevent duplicate records in dimension tables  
- **Referential integrity**: Validate foreign key relationships
- **Business logic**: Custom tests for domain-specific rules (e.g., sleep duration bounds)
- **Freshness checks**: Alert on stale data beyond acceptable thresholds

## Performance Considerations

- **Incremental processing**: Only new/changed records processed in daily runs
- **Columnar storage**: DuckDB optimized for analytical queries
- **Partitioning**: Data partitioned by date for efficient historical analysis
- **Indexing**: Strategic indexes on commonly filtered columns

---

**Built by Ryan Kirsch** | [Portfolio](https://ryankirsch.dev) | [LinkedIn](https://linkedin.com/in/ryankirsch) | [GitHub](https://github.com/agalloch88)

*This pipeline processes real personal data to demonstrate production-ready data engineering capabilities for analytical workloads.*