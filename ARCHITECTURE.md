# Data Engineering Portfolio Project: Multi-Source Health & Activity Analytics Pipeline

## Executive Summary

This portfolio project demonstrates end-to-end data engineering skills through a modern, asset-centric pipeline that combines personal health data (Oura Ring), weather patterns (OpenWeatherMap), and software development activity (GitHub) to create a comprehensive personal analytics dashboard. The architecture leverages cutting-edge tools and demonstrates real-world data engineering best practices.

**What makes this impressive:** Unlike typical DE portfolios using toy datasets, this combines personal health data with environmental and behavioral patterns, showcasing data storytelling, privacy-conscious design, and modern Python-native orchestration.

---

## 🎯 Data Sources Selection

### 1. Oura Ring API (Primary - Personal Health Data)
- **Why:** Ryan owns an Oura Ring, making this authentic personal data
- **Data richness:** Sleep stages, heart rate variability, activity levels, readiness scores
- **API limits:** 5,000 requests per 5-minute period (very generous)
- **Updates:** Multiple times daily (sleep, activity, readiness)
- **Uniqueness:** Personal health data pipelines are rare in portfolios
- **Data types:** Sleep metrics, activity data, readiness scores, heart rate data

### 2. OpenWeatherMap API (Environmental Context)
- **Why:** Weather correlates with sleep quality, activity levels, mood
- **Data richness:** Current conditions, forecasts, air quality, UV index
- **API limits:** 1,000 calls per day (sufficient for hourly collection)
- **Updates:** Hourly updates available
- **Business value:** Environmental factors impact health and productivity
- **Data types:** Temperature, humidity, air quality, precipitation, UV index

### 3. GitHub API (Professional Activity)
- **Why:** Developer activity patterns, productivity cycles, work-life balance
- **Data richness:** Commits, pull requests, issue activity, repository metrics
- **API limits:** 5,000 requests per hour (authenticated)
- **Updates:** Real-time as development happens
- **Portfolio relevance:** Shows understanding of developer workflow data
- **Data types:** Commit frequency, coding hours, repository activity, collaboration metrics

---

## 🏗️ Architecture Stack

### **Orchestration: Dagster** ⭐
**Rationale:** Asset-centric approach perfect for data engineering portfolios
- **Why over Prefect:** Data assets as first-class citizens, better for data-focused workflows
- **Modern approach:** Software-defined assets (SDAs) vs traditional task DAGs
- **Portfolio appeal:** Shows understanding of next-gen orchestration paradigms
- **Features:** Built-in data quality monitoring, asset lineage, type safety
- **Learning curve:** Medium, but demonstrates advanced DE thinking

### **Storage: DuckDB** ⭐
**Rationale:** Lightweight, high-performance analytics database
- **Why over Supabase:** Better for analytics workloads, no hosting costs
- **Performance:** Columnar storage, vectorized execution, excellent for aggregations
- **Portfolio benefits:** Shows understanding of OLAP vs OLTP trade-offs
- **Local development:** Easy setup, no cloud dependencies
- **dbt compatibility:** Native support, excellent performance

### **Transformation: dbt Core**
**Rationale:** Industry standard, demonstrates SQL skills and data modeling
- **Medallion architecture:** Bronze (raw) → Silver (cleaned) → Gold (business logic)
- **Version control:** Git-based workflow, code reviews
- **Testing:** Built-in data quality tests
- **Documentation:** Auto-generated docs with lineage graphs

### **Ingestion: Custom Python Scripts**
**Rationale:** More impressive than drag-and-drop tools, shows coding skills
- **API clients:** Custom async Python for each data source
- **Error handling:** Retry logic, rate limiting, graceful failures
- **Data validation:** Pydantic models for type safety
- **Incremental loads:** Track watermarks, avoid duplicate data

### **Visualization: Evidence.dev** ⭐
**Rationale:** Modern BI-as-code tool, differentiates from typical Streamlit portfolios
- **Why over Streamlit:** Better for report-style dashboards, SQL-native
- **Git-based:** Dashboards in version control
- **Performance:** Pre-computed queries, fast loading
- **Professional look:** Clean, report-style layouts

---

## 📊 Project Scope & MVP Definition

### **Data Models (7 dbt models)**

#### Bronze Layer (Raw Data)
1. `bronze_oura_sleep` - Raw sleep session data
2. `bronze_oura_activity` - Raw daily activity metrics
3. `bronze_weather_hourly` - Raw hourly weather observations
4. `bronze_github_commits` - Raw commit and repository activity

#### Silver Layer (Cleaned & Enriched)
5. `silver_daily_health_metrics` - Cleaned daily health aggregations
6. `silver_weather_daily` - Daily weather summaries with derived metrics

#### Gold Layer (Business Logic)
7. `gold_health_weather_correlations` - Combined health + environmental insights

### **Key Visualizations (5 Dashboard Components)**

1. **Sleep Quality Heatmap** - Sleep scores vs weather conditions over time
2. **Activity vs Weather Correlation** - How weather affects movement patterns
3. **Productivity Cycles** - GitHub activity patterns vs health metrics
4. **Weekly Health Trends** - Rolling averages, trend detection
5. **Environmental Impact Dashboard** - Air quality vs HRV, temperature vs sleep

### **Technical Features**
- **Automated scheduling:** Daily pipeline runs via Dagster schedules
- **Data quality monitoring:** dbt tests + Dagster asset checks
- **Incremental loading:** Only process new data since last run
- **Error alerting:** Slack notifications for pipeline failures
- **Performance monitoring:** Pipeline execution metrics and optimization

---

## 🚀 Phased Build Plan

### **Phase 1: Foundation (Week 1)**
- [ ] Set up development environment (Python, dbt, DuckDB, Dagster)
- [ ] Create API clients for all three data sources
- [ ] Build basic ingestion pipeline for Oura Ring data
- [ ] Set up dbt project structure with bronze layer
- [ ] Create initial data quality tests

### **Phase 2: Core Pipeline (Week 2)**
- [ ] Complete ingestion for weather and GitHub APIs
- [ ] Build silver layer transformations
- [ ] Implement incremental loading strategies
- [ ] Add comprehensive dbt testing suite
- [ ] Set up Dagster asset materialization

### **Phase 3: Analytics Layer (Week 3)**
- [ ] Create gold layer models with business logic
- [ ] Build correlation analysis between data sources
- [ ] Implement data quality monitoring
- [ ] Add performance optimization (indexes, partitioning)
- [ ] Create Dagster sensors for real-time updates

### **Phase 4: Visualization & Polish (Week 4)**
- [ ] Set up Evidence.dev project
- [ ] Build all 5 key dashboard components
- [ ] Create comprehensive README with architecture diagrams
- [ ] Add monitoring and alerting
- [ ] Deploy to cloud (optional: GitHub Actions + cloud hosting)

---

## 🌟 Why This Project Stands Out

### **1. Personal Data Storytelling**
- Uses real, personal data rather than contrived datasets
- Demonstrates privacy-conscious data engineering practices
- Shows how data engineering enables personal insights

### **2. Modern Tool Selection**
- **Dagster:** Next-generation orchestration (vs outdated Airflow)
- **DuckDB:** High-performance analytics database
- **Evidence.dev:** Modern BI-as-code approach
- Shows awareness of current industry trends

### **3. Cross-Domain Data Integration**
- Health + Environment + Professional activity
- Demonstrates complex data relationships
- Shows business value through correlation analysis

### **4. Production-Ready Practices**
- Comprehensive testing at every layer
- Error handling and monitoring
- Version controlled transformations
- Performance optimization

### **5. Technical Depth**
- Custom API integrations (not pre-built connectors)
- Advanced dbt patterns (incremental models, macros, tests)
- Asset-centric orchestration paradigm
- Modern Python practices (async, type hints, Pydantic)

---

## 🎯 Success Metrics

### **Technical Metrics**
- Pipeline reliability: >99% success rate
- Data freshness: <2 hour latency for all sources
- Test coverage: >90% of data models have quality tests
- Performance: Full refresh completes in <5 minutes

### **Portfolio Impact Metrics**
- Demonstrates 7+ modern data engineering tools
- Shows end-to-end pipeline ownership
- Exhibits both technical skills and business understanding
- Includes comprehensive documentation and architecture diagrams

---

## 🔧 Implementation Notes

### **Development Environment Setup**
```bash
# Core dependencies
pip install dagster dbt-duckdb evidence-dev requests pydantic

# API client libraries
pip install oura-ring openweather-python pygithub

# Development tools
pip install black flake8 pytest pre-commit
```

### **Key Architecture Decisions**
1. **Local-first development:** DuckDB enables full local testing
2. **Asset-centric orchestration:** Dagster SDAs over traditional DAGs
3. **SQL-heavy transformations:** dbt for data modeling, Python for ingestion only
4. **Markdown-based reporting:** Evidence.dev for maintainable dashboards

### **Scalability Considerations**
- DuckDB handles millions of rows efficiently for this use case
- Easy migration path to MotherDuck for cloud scaling
- Dagster supports distributed execution when needed
- API rate limits sufficient for personal use case

---

## 📈 Future Enhancement Opportunities

### **Phase 2 Expansions (Post-Portfolio)**
- Add financial data (bank transactions, investment performance)
- Integrate social media sentiment analysis
- Include nutrition tracking (MyFitnessPal API)
- Add machine learning predictions (sleep quality forecasting)

### **Technical Improvements**
- Containerization with Docker
- CI/CD pipeline with GitHub Actions
- Real-time streaming with Kafka
- Advanced analytics with ML pipelines

This architecture demonstrates comprehensive data engineering skills while creating genuine business value through personal health and productivity insights. The combination of modern tooling, real data sources, and production-ready practices makes it a standout portfolio piece in today's competitive market.