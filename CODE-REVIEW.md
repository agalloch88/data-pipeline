# Code Review: Data Pipeline Project

**Reviewer:** Knox (QA Engineer)  
**Date:** 2026-02-19  
**Review Scope:** Complete data engineering pipeline - Dagster assets, dbt models, scripts, and dependencies

---

## 🔴 Critical Issues (Fix Before Portfolio Review)

### 1. **Critical SQL Error in `stg_oura_activity.sql`**
**File:** `dbt_project/models/staging/stg_oura_activity.sql`  
**Issue:** Model is pulling from wrong source table

```sql
-- WRONG: This pulls from sleep data, not activity data
select
  id,
  cast(day as date) as day,
  try_cast(time_in_bed as double) as time_in_bed,
  ...
from main.raw_oura_sleep  -- ❌ Should be raw_oura_activity
```

**Impact:** This would cause incorrect data in all downstream models and break the entire analytics pipeline.

**Fix Required:** Create proper `oura_activity_data` Dagster asset and correct the SQL source reference.

### 2. **Missing Critical Asset: `oura_activity_data`**
**File:** `pipeline_assets/assets/oura.py`  
**Issue:** dbt models reference `raw_oura_activity` table, but no corresponding Dagster asset exists

**Impact:** `stg_oura_activity` model will fail at runtime with "table not found" error.

**Fix Required:** Implement `oura_activity_data` asset to fetch Oura Activity API data.

### 3. **Data Structure Mismatches in SQL Models**
**Files:** 
- `dbt_project/models/staging/stg_github_commits.sql`
- `dbt_project/models/staging/stg_weather_daily.sql`

**Issues:**
```sql
-- GitHub model assumes raw JSON column, but asset stores structured data
select json->>'sha' as sha  -- ❌ Won't work with read_json_auto()

-- Weather model tries to parse already-parsed JSON
try_cast(json_extract(main, '$.temp') as double)  -- ❌ 'main' is already a struct
```

**Fix Required:** Align SQL queries with actual DuckDB schema created by `read_json_auto()`.

### 4. **Incomplete Asset Exports**
**File:** `pipeline_assets/assets/__init__.py`  
**Issue:** Missing export for `oura_activity_data` and possible other assets

**Fix Required:** Add all assets to `__all__` list for proper Dagster discovery.

---

## 🟡 Major Issues (High Priority)

### 5. **Missing Dagster Resources Configuration**
**File:** `pipeline_assets/__init__.py`  
**Issue:** No DuckDB resource defined, assets use hardcoded database paths

```python
# Missing resource definition
from dagster_duckdb import DuckDBResource

definitions = Definitions(
    assets=all_assets,
    schedules=[daily_schedule],
    resources={
        "duckdb": DuckDBResource(database="data/pipeline.duckdb")
    }
)
```

**Impact:** Poor separation of concerns, difficulty in testing, no environment-specific configuration.

### 6. **Hardcoded Configuration in Runner Script**
**File:** `scripts/run_pipeline.sh`  
**Issues:**
- Hardcoded username: `GITHUB_USERNAME="youvereachedhenryjones"`
- Hardcoded coordinates: `WEATHER_LAT="35.2271"`
- Assumes specific secret paths: `~/.openclaw/.secrets/`

**Impact:** Script won't work in other environments or for other users.

**Fix:** Use environment variables with defaults, make configuration portable.

### 7. **Poor Error Handling in Assets**
**Files:** All asset files in `pipeline_assets/assets/`  
**Issue:** Assets raise exceptions that fail entire pipeline instead of graceful degradation

```python
# Current approach fails entire pipeline
except requests.RequestException as exc:
    logger.error("API request failed: %s", exc)
    raise  # ❌ Kills entire pipeline

# Better approach
except requests.RequestException as exc:
    logger.warning("API request failed, skipping: %s", exc)
    return MaterializeResult(metadata={"status": "skipped_api_error"})
```

### 8. **JSON Parsing Errors in Oura Model**
**File:** `dbt_project/models/staging/stg_oura_sleep.sql`  
**Issue:** Attempts to access nested JSON with dot notation

```sql
-- This will likely fail
try_cast(readiness.score as double) as score,
try_cast(readiness.temperature_deviation as double) as temperature_delta
```

**Fix:** Use proper JSON extraction functions or flatten during asset creation.

---

## 🟠 Code Quality Issues (Medium Priority)

### 9. **Inconsistent Python Code Style**
**Issues:**
- Missing type hints on main asset functions
- Inconsistent error message formatting
- Some docstrings missing or incomplete

**Example Fix:**
```python
from typing import Dict, Any

@asset(description="Fetches Oura sleep data...")
def oura_sleep_data() -> MaterializeResult:
    """Fetch last 7 days of Oura sleep data and store in DuckDB."""
```

### 10. **Hardcoded File Paths**
**Files:** All asset files  
**Issue:** Using `Path(__file__).resolve().parents[2]` for project root

**Fix:** Use environment variables or Dagster resources for file paths.

### 11. **Missing Input Validation**
**Issue:** No validation of API response structure before processing

**Fix:** Add Pydantic models for API response validation:
```python
from pydantic import BaseModel
from typing import List, Optional

class OuraSleepRecord(BaseModel):
    id: str
    day: str
    total_sleep_duration: Optional[int]
    # ... other fields
```

---

## ✅ What's Working Well

### **Strong Architecture Decisions**
- Excellent choice of modern tools (Dagster, DuckDB, dbt)
- Clear separation of concerns (ELT pattern)
- Good dbt model layering (staging → intermediate → marts)
- Comprehensive test coverage in schema files

### **Good SQL Practices**
- Proper use of CTEs in intermediate models
- Reasonable join strategies and aggregations
- Good column naming conventions
- Appropriate data type casting with `try_cast()`

### **Professional Project Structure**
- Well-organized directory structure
- Comprehensive README with clear setup instructions
- Good dependency management in `pyproject.toml`
- Helpful setup and run scripts

### **Modern dbt Patterns**
- Proper use of `{{ ref() }}` for model dependencies
- Good materialization strategies (views for staging, tables for marts)
- Comprehensive schema documentation
- Appropriate data quality tests

---

## 🛠️ Recommended Fixes

### **Immediate (Before Portfolio Review)**

1. **Create missing `oura_activity_data` asset**
2. **Fix `stg_oura_activity.sql` to pull from correct table**
3. **Fix JSON parsing in staging models**
4. **Add DuckDB resource to Dagster definitions**
5. **Make runner script configurable (remove hardcoded values)**

### **High Priority**

1. **Implement graceful error handling** in all assets
2. **Add proper type hints and validation**
3. **Fix JSON structure assumptions** in dbt models
4. **Add comprehensive logging** throughout pipeline

### **Nice to Have**

1. **Add unit tests** for asset functions
2. **Implement incremental dbt models** for better performance  
3. **Add data quality monitoring** with Dagster asset checks
4. **Create environment-specific configurations**

---

## 📊 Security Assessment

### ✅ **Good Security Practices**
- API tokens loaded from environment variables
- No hardcoded credentials in code
- Proper gitignore excluding secrets

### ⚠️ **Security Improvements Needed**
- Add input sanitization for API responses
- Implement rate limiting and retry logic
- Add proper access controls for database files

---

## 🎯 Final Assessment

**Overall Quality:** B+ (Good foundation, critical bugs need fixes)

**Strengths:**
- Excellent architecture and tool selection
- Professional project structure and documentation  
- Good understanding of modern data engineering patterns
- Comprehensive dbt modeling approach

**Critical Path to Success:**
1. Fix the SQL data source mismatches (highest priority)
2. Create missing Oura activity asset
3. Implement graceful error handling
4. Test end-to-end pipeline execution

**Portfolio Readiness:** After fixing the critical issues, this will be an impressive portfolio project that demonstrates modern data engineering skills with real-world complexity.

---

*This review focused on code quality, architectural soundness, and production readiness. The project shows strong potential and good engineering practices, with several critical bugs that need addressing before showcasing to hiring managers.*