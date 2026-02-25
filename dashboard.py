import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Pipeline Dashboard", layout="wide")

DB_PATH = Path(__file__).resolve().parent / "data" / "pipeline.duckdb"


def query_table(table_name: str, query: str):
    """Run a query against DuckDB and return (rows, columns)."""
    try:
        with duckdb.connect(str(DB_PATH), read_only=True) as con:
            result = con.execute(query)
            rows = result.fetchall()
            columns = [col[0] for col in result.description]
        return rows, columns
    except Exception as exc:  # noqa: BLE001
        message = str(exc).lower()
        if "table" in message and ("not found" in message or "does not exist" in message):
            st.info(f"Table `{table_name}` not found or unavailable.")
        elif "catalog" in message and "error" in message:
            st.info(f"Table `{table_name}` not found or unavailable.")
        else:
            st.info(f"Unable to query `{table_name}`.")
        return None, None


def to_df(rows, columns):
    if rows is None or columns is None:
        return None
    return pd.DataFrame(rows, columns=columns)


def seconds_to_hours(series):
    return series / 3600.0


def find_first_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Daily Wellness",
        "Weekly Summary",
        "Sleep Analysis",
        "GitHub Activity",
        "Correlations",
    ],
)

st.title("Pipeline Dashboard")

if page == "Daily Wellness":
    st.subheader("Daily Wellness")

    rows, cols = query_table(
        "mart_daily_wellness",
        "select * from mart_daily_wellness order by 1",
    )
    df = to_df(rows, cols)

    if df is not None and not df.empty:
        date_col = find_first_column(cols, ["day", "date", "ds", "timestamp"])
        efficiency_col = find_first_column(cols, ["efficiency", "sleep_efficiency"])
        readiness_col = find_first_column(cols, ["readiness_score", "readiness", "score"])
        hr_col = find_first_column(cols, ["average_heart_rate", "avg_heart_rate", "hr"])

        if date_col is None or efficiency_col is None or readiness_col is None or hr_col is None:
            st.info("mart_daily_wellness is missing expected columns.")
        else:
            df = df.sort_values(date_col)
            latest = df.iloc[-1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Sleep Efficiency", f"{latest[efficiency_col]:.1f}")
            c2.metric("Readiness Score", f"{latest[readiness_col]:.1f}")
            c3.metric("Avg Heart Rate", f"{latest[hr_col]:.1f}")

            plot_df = df[[date_col, efficiency_col, readiness_col, hr_col]].melt(
                id_vars=[date_col],
                var_name="metric",
                value_name="value",
            )
            fig = px.line(
                plot_df,
                x=date_col,
                y="value",
                color="metric",
                template="plotly_dark",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        rows, cols = query_table(
            "raw_oura_sleep",
            """
            select
                day,
                efficiency,
                readiness.score as readiness_score,
                average_heart_rate
            from raw_oura_sleep
            order by day
            """,
        )
        df = to_df(rows, cols)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Sleep Efficiency", f"{latest['efficiency']:.1f}")
            c2.metric("Readiness Score", f"{latest['readiness_score']:.1f}")
            c3.metric("Avg Heart Rate", f"{latest['average_heart_rate']:.1f}")

            plot_df = df.melt(
                id_vars=["day"],
                var_name="metric",
                value_name="value",
            )
            fig = px.line(
                plot_df,
                x="day",
                y="value",
                color="metric",
                template="plotly_dark",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)

elif page == "Weekly Summary":
    st.subheader("Weekly Summary")

    rows, cols = query_table(
        "mart_weekly_summary",
        "select * from mart_weekly_summary order by 1",
    )
    df = to_df(rows, cols)

    if df is not None and not df.empty:
        week_col = find_first_column(cols, ["week_start", "week", "week_date"])
        duration_col = find_first_column(cols, ["avg_sleep_duration", "avg_sleep_hours"])
        efficiency_col = find_first_column(cols, ["avg_efficiency", "sleep_efficiency"])

        if week_col is None or duration_col is None or efficiency_col is None:
            st.info("mart_weekly_summary is missing expected columns.")
        else:
            plot_df = df[[week_col, duration_col, efficiency_col]].copy()
            if duration_col == "avg_sleep_duration":
                plot_df[duration_col] = seconds_to_hours(plot_df[duration_col])
            plot_df = plot_df.melt(
                id_vars=[week_col],
                var_name="metric",
                value_name="value",
            )
            fig = px.bar(
                plot_df,
                x=week_col,
                y="value",
                color="metric",
                barmode="group",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        rows, cols = query_table(
            "raw_oura_sleep",
            """
            select
                date_trunc('week', day) as week_start,
                avg(total_sleep_duration) / 3600.0 as avg_sleep_hours,
                avg(efficiency) as avg_efficiency
            from raw_oura_sleep
            group by 1
            order by 1
            """,
        )
        df = to_df(rows, cols)
        if df is not None and not df.empty:
            plot_df = df.melt(
                id_vars=["week_start"],
                var_name="metric",
                value_name="value",
            )
            fig = px.bar(
                plot_df,
                x="week_start",
                y="value",
                color="metric",
                barmode="group",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

elif page == "Sleep Analysis":
    st.subheader("Sleep Analysis")

    rows, cols = query_table(
        "raw_oura_sleep",
        """
        select
            day,
            total_sleep_duration,
            deep_sleep_duration,
            rem_sleep_duration,
            light_sleep_duration,
            average_heart_rate
        from raw_oura_sleep
        order by day
        """,
    )
    df = to_df(rows, cols)
    if df is not None and not df.empty:
        df = df.sort_values("day")
        df["total_sleep_hours"] = seconds_to_hours(df["total_sleep_duration"])
        df["deep_sleep_hours"] = seconds_to_hours(df["deep_sleep_duration"])
        df["rem_sleep_hours"] = seconds_to_hours(df["rem_sleep_duration"])
        df["light_sleep_hours"] = seconds_to_hours(df["light_sleep_duration"])

        fig_total = px.line(
            df,
            x="day",
            y="total_sleep_hours",
            template="plotly_dark",
            markers=True,
        )
        st.plotly_chart(fig_total, use_container_width=True)

        breakdown_df = df[["day", "deep_sleep_hours", "rem_sleep_hours", "light_sleep_hours"]].melt(
            id_vars=["day"],
            var_name="stage",
            value_name="hours",
        )
        fig_stack = px.bar(
            breakdown_df,
            x="day",
            y="hours",
            color="stage",
            barmode="stack",
            template="plotly_dark",
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        fig_hr = px.line(
            df,
            x="day",
            y="average_heart_rate",
            template="plotly_dark",
            markers=True,
        )
        st.plotly_chart(fig_hr, use_container_width=True)

elif page == "GitHub Activity":
    st.subheader("GitHub Activity")

    rows, cols = query_table("stg_github_commits", "select * from stg_github_commits limit 1")
    if cols is not None:
        date_col = find_first_column(
            cols,
            [
                "commit_date",
                "committed_date",
                "authored_date",
                "date",
                "timestamp",
                "created_at",
            ],
        )
        if date_col is not None:
            rows, cols = query_table(
                "stg_github_commits",
                f"""
                select
                    date_trunc('day', cast({date_col} as timestamp)) as day,
                    count(*) as commits
                from stg_github_commits
                group by 1
                order by 1
                """,
            )
            df = to_df(rows, cols)
            if df is not None and not df.empty:
                fig = px.bar(
                    df,
                    x="day",
                    y="commits",
                    template="plotly_dark",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No GitHub data available yet.")
        else:
            st.info("No GitHub data available yet.")
    else:
        rows, cols = query_table(
            "raw_github_commits",
            """
            select
                date_trunc('day', cast(json_extract(json, '$.commit.committer.date') as timestamp)) as day,
                count(*) as commits
            from raw_github_commits
            group by 1
            order by 1
            """,
        )
        df = to_df(rows, cols)
        if df is not None and not df.empty:
            fig = px.bar(
                df,
                x="day",
                y="commits",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No GitHub data available yet.")

elif page == "Correlations":
    st.subheader("Correlations")

    rows, cols = query_table(
        "raw_oura_sleep",
        """
        select
            total_sleep_duration,
            efficiency,
            average_heart_rate
        from raw_oura_sleep
        """,
    )
    df = to_df(rows, cols)
    if df is not None and not df.empty:
        df["sleep_hours"] = seconds_to_hours(df["total_sleep_duration"])

        fig_eff = px.scatter(
            df,
            x="sleep_hours",
            y="efficiency",
            template="plotly_dark",
        )
        st.plotly_chart(fig_eff, use_container_width=True)

        fig_hr = px.scatter(
            df,
            x="sleep_hours",
            y="average_heart_rate",
            template="plotly_dark",
        )
        st.plotly_chart(fig_hr, use_container_width=True)

