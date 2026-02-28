"""Run Great Expectations validations against health pipeline staging data."""

from __future__ import annotations

import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
GX_DIR = Path(__file__).resolve().parents[1] / "gx"
DB_PATH = DATA_DIR / "pipeline.duckdb"

# Maps suite name to the DuckDB staging query
SUITE_TO_QUERY = {
    "oura_sleep_suite": "SELECT * FROM main.stg_oura_sleep",
    "oura_activity_suite": "SELECT * FROM main.stg_oura_activity",
    "weather_daily_suite": "SELECT * FROM main.stg_weather_daily",
}


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)


def _load_dataframe(query: str):
    import duckdb

    if not DB_PATH.exists():
        _print_error(f"ERROR: DuckDB database not found at {DB_PATH}")
        _print_error("Run the Dagster pipeline first to populate data.")
        return None

    connection = duckdb.connect(database=str(DB_PATH), read_only=True)
    try:
        return connection.execute(query).df()
    except Exception as exc:
        _print_error(f"ERROR: Query failed: {query}")
        _print_error(f"Details: {exc.__class__.__name__}: {exc}")
        return None
    finally:
        connection.close()


def _get_context():
    try:
        import great_expectations as gx
    except Exception as exc:
        _print_error("ERROR: Great Expectations failed to import.")
        _print_error(
            "This environment uses Python 3.14, and Great Expectations 0.18.8 may "
            "not be compatible (pydantic dependency conflicts are common)."
        )
        _print_error("Try running with Python <= 3.13 or upgrading Great Expectations.")
        _print_error(f"Details: {exc.__class__.__name__}: {exc}")
        return None

    try:
        return gx.get_context(context_root_dir=str(GX_DIR))
    except Exception as exc:
        _print_error("ERROR: Unable to initialize Great Expectations context.")
        _print_error(f"Details: {exc.__class__.__name__}: {exc}")
        return None


def main() -> int:
    if not DB_PATH.exists():
        _print_error(f"DuckDB database not found at {DB_PATH}")
        _print_error("Run the Dagster pipeline first: dagster dev")
        return 2

    context = _get_context()
    if context is None:
        return 3

    try:
        datasource = context.sources.add_or_update_pandas(name="pandas")
    except AttributeError:
        datasource = context.sources.add_pandas(name="pandas")

    overall_success = True
    for suite_name, query in SUITE_TO_QUERY.items():
        dataframe = _load_dataframe(query)
        if dataframe is None:
            _print_error(f"SKIP: {suite_name} (no data)")
            continue

        if dataframe.empty:
            print(f"{suite_name}: SKIP (0 rows)")
            continue

        asset = datasource.add_dataframe_asset(name=suite_name)
        batch_request = asset.build_batch_request(dataframe=dataframe)

        try:
            suite = context.get_expectation_suite(suite_name)
        except Exception as exc:
            _print_error(f"ERROR: Unable to load expectation suite '{suite_name}'.")
            _print_error(f"Details: {exc.__class__.__name__}: {exc}")
            overall_success = False
            continue

        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite=suite,
        )
        result = validator.validate()

        success = bool(result.get("success"))
        overall_success = overall_success and success
        status = "PASS" if success else "FAIL"
        rows = len(dataframe)
        print(f"{suite_name}: {status} ({rows} rows)")

        if not success:
            stats = result.get("statistics", {})
            print(
                "  evaluated={evaluated} passed={passed} failed={failed}".format(
                    evaluated=stats.get("evaluated_expectations"),
                    passed=stats.get("successful_expectations"),
                    failed=stats.get("unsuccessful_expectations"),
                )
            )

    print(f"Overall: {'PASS' if overall_success else 'FAIL'}")
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
