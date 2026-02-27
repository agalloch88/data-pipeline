"""Run Great Expectations validations against staging data."""

from __future__ import annotations

import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
GX_DIR = Path(__file__).resolve().parents[1] / "gx"

SUITE_TO_CSV = {
    "orders_suite": "orders.csv",
    "customers_suite": "customers.csv",
    "products_suite": "products.csv",
}


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)


def _load_dataframe(csv_path: Path):
    import duckdb

    connection = duckdb.connect(database=":memory:")
    try:
        return connection.execute(
            "select * from read_csv_auto(?)",
            [str(csv_path)],
        ).df()
    finally:
        connection.close()


def _get_context():
    try:
        import great_expectations as gx
    except Exception as exc:  # pragma: no cover - runtime compatibility guard
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
    missing = [
        csv_name
        for csv_name in SUITE_TO_CSV.values()
        if not (DATA_DIR / csv_name).exists()
    ]

    if missing:
        _print_error("Missing expected CSV sources under data/:")
        for csv_name in missing:
            _print_error(f"- data/{csv_name}")
        _print_error(
            "Safer behavior: not generating sample data automatically. "
            "Create the CSVs above to run validations."
        )
        return 2

    context = _get_context()
    if context is None:
        return 3

    try:
        datasource = context.sources.add_or_update_pandas(name="pandas")
    except AttributeError:
        datasource = context.sources.add_pandas(name="pandas")

    overall_success = True
    for suite_name, csv_name in SUITE_TO_CSV.items():
        csv_path = DATA_DIR / csv_name
        dataframe = _load_dataframe(csv_path)

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
        print(f"{suite_name}: {status}")

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
