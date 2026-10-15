
import os

import pandas as pd
import requests
import streamlit as st


DEFAULT_API_URL = (
    "https://ai-data-quality-validator-api.onrender.com"
)

API_URL = os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")
MAX_FILE_SIZE = 10 * 1024 * 1024

st.set_page_config(
    page_title="AI Data Quality Validator",
    page_icon="🔎",
    layout="wide",
)


def format_number(value):
    """Format numeric values for dashboard display."""
    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass

    if isinstance(value, (int, float)):
        return f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"

    return str(value)


def api_health():
    """Check whether the API is reachable."""
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=60,
        )
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as exc:
        return False, str(exc)
    except ValueError as exc:
        return False, f"Invalid health response: {exc}"


def submit_csv(uploaded_file):
    """Send a CSV upload to the FastAPI backend."""
    try:
        response = requests.post(
            f"{API_URL}/upload-csv",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "text/csv",
                )
            },
            timeout=(15, 240),
        )

        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text

            return None, f"API error ({response.status_code}): {detail}"

        result = response.json()

        if not isinstance(result, dict):
            return None, "The API returned an unexpected response format."

        return result, None

    except requests.Timeout:
        return None, (
            "The request timed out. The API may be starting up or "
            "processing the dataset. Please try again."
        )
    except requests.RequestException as exc:
        return None, f"Could not connect to the API: {exc}"
    except ValueError:
        return None, "The API returned an invalid JSON response."


def render_overview(summary):
    """Display high-level validation metrics."""
    columns = st.columns(4)

    metrics = [
        ("Records", summary.get("total_records", 0)),
        ("Columns", summary.get("total_columns", 0)),
        ("Findings", summary.get("total_issues", 0)),
        ("Affected records", summary.get("affected_records", 0)),
    ]

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, format_number(value))


def render_severity(summary):
    """Display issue counts by severity."""
    st.subheader("Findings by severity")

    severity = summary.get("issues_by_severity") or {}

    if not isinstance(severity, dict) or not severity:
        st.info("No validation findings were recorded.")
        return

    severity_df = pd.DataFrame(
        [
            {"Severity": level, "Count": count}
            for level, count in severity.items()
        ]
    )

    st.bar_chart(severity_df.set_index("Severity"), y="Count")


def render_rules(summary):
    """Display issue counts by validation rule."""
    st.subheader("Findings by validation rule")

    rules = summary.get("issues_by_rule") or {}

    if not isinstance(rules, dict) or not rules:
        st.info("No validation rules produced findings.")
        return

    rules_df = pd.DataFrame(
        [
            {"Rule": rule, "Count": count}
            for rule, count in rules.items()
        ]
    ).sort_values("Count", ascending=False)

    st.bar_chart(rules_df.set_index("Rule"), y="Count")
    st.dataframe(rules_df, use_container_width=True, hide_index=True)


def render_dataset_overview(statistics):
    """Display generic dataset statistics."""
    st.subheader("Dataset statistics")

    overview = statistics.get("dataset_overview") or {}

    metrics = [
        ("Duplicate rows", overview.get("duplicate_row_count", 0)),
        ("Missing cells", overview.get("total_missing_cells", 0)),
        ("Total cells", overview.get("total_cells", 0)),
        (
            "Memory usage",
            f"{format_number(overview.get('memory_usage_bytes', 0))} bytes",
        ),
    ]

    columns = st.columns(4)

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


def normalize_top_values(top_values):
    """Convert different top-values formats into a displayable DataFrame."""
    if top_values is None:
        return pd.DataFrame()

    if isinstance(top_values, dict):
        if not top_values:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {"Value": str(value), "Count": count}
                for value, count in top_values.items()
            ]
        )

    if isinstance(top_values, list):
        if not top_values:
            return pd.DataFrame()

        if all(isinstance(item, dict) for item in top_values):
            return pd.DataFrame(top_values)

        rows = []

        for item in top_values:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                rows.append({"Value": str(item[0]), "Count": item[1]})
            else:
                rows.append({"Value": str(item)})

        return pd.DataFrame(rows)

    return pd.DataFrame({"Value": [str(top_values)]})


def render_column_profiles(statistics):
    """Display profiles for every dataset column."""
    st.subheader("Column profiles")

    profiles = statistics.get("columns") or []

    if not profiles:
        st.info("No column profiles are available.")
        return

    profile_rows = []

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        row = {
            "Column": profile.get("column", ""),
            "Data type": profile.get("data_type", ""),
            "Profile type": profile.get("profile_type", ""),
            "Non-missing": profile.get("non_missing_count", 0),
            "Missing": profile.get("missing_count", 0),
            "Missing %": profile.get("missing_percent", 0),
            "Unique values": profile.get("unique_count", 0),
            "Unique %": profile.get("unique_percent", 0),
        }

        numeric_stats = profile.get("statistics") or {}

        if isinstance(numeric_stats, dict) and numeric_stats:
            row.update({
                "Mean": numeric_stats.get("mean"),
                "Median": numeric_stats.get("median"),
                "Minimum": numeric_stats.get("min"),
                "Maximum": numeric_stats.get("max"),
                "Outliers (IQR)": numeric_stats.get("outlier_count_iqr"),
            })

        date_stats = profile.get("date_statistics") or {}

        if isinstance(date_stats, dict) and date_stats:
            row["Earliest date"] = date_stats.get("min")
            row["Latest date"] = date_stats.get("max")

        profile_rows.append(row)

    if not profile_rows:
        st.info("No usable column profiles were returned.")
        return

    profile_df = pd.DataFrame(profile_rows)

    st.dataframe(
        profile_df,
        use_container_width=True,
        hide_index=True,
    )

    available_profiles = [
        profile
        for profile in profiles
        if isinstance(profile, dict) and profile.get("column") is not None
    ]

    if not available_profiles:
        return

    selected_column = st.selectbox(
        "Explore a column",
        options=[profile["column"] for profile in available_profiles],
    )

    selected_profile = next(
        (
            profile
            for profile in available_profiles
            if profile.get("column") == selected_column
        ),
        None,
    )

    if selected_profile:
        with st.expander(
            f"Detailed profile: {selected_column}",
            expanded=True,
        ):
            st.json(selected_profile)

            top_values = selected_profile.get("top_values")
            top_values_df = normalize_top_values(top_values)

            if not top_values_df.empty:
                st.write("Most frequent values")
                st.dataframe(
                    top_values_df,
                    use_container_width=True,
                    hide_index=True,
                )


def render_correlations(statistics):
    """Display numeric correlations when available."""
    st.subheader("Numeric correlations")

    correlations = statistics.get("numeric_correlations") or {}

    if not isinstance(correlations, dict) or not correlations:
        st.info("No numeric correlations are available for this dataset.")
        return

    correlation_df = pd.DataFrame(correlations)

    if correlation_df.empty:
        st.info("No correlation data is available.")
        return

    st.dataframe(correlation_df, use_container_width=True)


def render_issues(issues):
    """Display detailed validation findings."""
    st.subheader("Detailed validation findings")

    if not issues:
        st.success(
            "No findings were detected by the current validation rules."
        )
        st.caption(
            "This does not guarantee that all values are correct or "
            "that every business rule has been checked."
        )
        return

    issues_df = pd.DataFrame(issues)

    if issues_df.empty:
        st.info("No detailed findings are available.")
        return

    filter_columns = st.columns(2)

    severity_options = (
        sorted(issues_df["severity"].dropna().unique().tolist())
        if "severity" in issues_df.columns
        else []
    )

    rule_options = (
        sorted(issues_df["rule"].dropna().unique().tolist())
        if "rule" in issues_df.columns
        else []
    )

    selected_severity = filter_columns[0].multiselect(
        "Filter by severity",
        options=severity_options,
        default=severity_options,
    )

    selected_rules = filter_columns[1].multiselect(
        "Filter by rule",
        options=rule_options,
        default=rule_options,
    )

    filtered_df = issues_df.copy()

    if "severity" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["severity"].isin(selected_severity)
        ]

    if "rule" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["rule"].isin(selected_rules)
        ]

    st.caption(
        f"Showing {len(filtered_df):,} of {len(issues_df):,} findings."
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )


def render_report(report):
    """Show and allow downloading the generated Markdown report."""
    st.subheader("Quality report")

    if not report:
        st.info("No report content was returned.")
        return

    st.markdown(report)

    st.download_button(
        label="Download quality report",
        data=report,
        file_name="data_quality_report.md",
        mime="text/markdown",
    )


st.title("🔎 AI-Powered Data Quality Validator")

st.markdown(
    """
Upload a CSV dataset to identify potential data quality problems,
explore statistical profiles, and generate actionable recommendations.

**Works with general-purpose tabular datasets** — no fixed company
schema is required.
"""
)

with st.sidebar:
    st.header("Configuration")
    st.write("API endpoint")
    st.code(API_URL)

    if st.button("Check API health", use_container_width=True):
        with st.spinner("Checking API connection..."):
            healthy, details = api_health()

        if healthy:
            st.success("API is reachable.")
            st.json(details)
        else:
            st.error("API is unavailable.")
            st.caption(str(details))

    st.divider()
    st.caption("Maximum upload size: 10 MB")

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Upload a CSV file containing the dataset you want to analyze.",
)

if uploaded_file is not None:
    st.caption(
        f"Selected file: {uploaded_file.name} "
        f"({uploaded_file.size:,} bytes)"
    )

    if uploaded_file.size == 0:
        st.error("The selected file is empty.")

    elif uploaded_file.size > MAX_FILE_SIZE:
        st.error("The maximum supported file size is 10 MB.")

    else:
        if st.button(
            "Analyze dataset",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(
                "Validating the dataset and generating insights..."
            ):
                result, error = submit_csv(uploaded_file)

            if error:
                st.error(error)
            else:
                st.session_state["analysis_result"] = result
                st.session_state["analysis_filename"] = uploaded_file.name
                st.success("Dataset analysis completed successfully!")

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]

    summary = result.get("summary") or {}
    statistics = summary.get("statistical_analysis") or {}
    issues = result.get("issues") or []
    report = result.get("report", "")
    evidence = result.get("evidence") or {}

    st.divider()

    st.header(
        f"Results: {st.session_state.get('analysis_filename', 'Dataset')}"
    )

    ai_status = result.get("ai_status", "unknown")

    if ai_status == "success":
        st.success("AI-generated insights are available.")

    elif ai_status == "fallback":
        st.warning(
            "The deterministic report is displayed because AI insights "
            "were unavailable. Validation results are still available."
        )

    else:
        st.info(f"Insight generation status: {ai_status}")

    tabs = st.tabs([
        "Overview",
        "Column profiles",
        "Validation findings",
        "AI report",
        "Evidence",
    ])

    with tabs[0]:
        render_overview(summary)
        render_severity(summary)
        render_rules(summary)
        render_dataset_overview(statistics)

    with tabs[1]:
        render_column_profiles(statistics)
        render_correlations(statistics)

    with tabs[2]:
        render_issues(issues)

    with tabs[3]:
        render_report(report)

    with tabs[4]:
        st.subheader("Evidence summary")
        st.json(evidence)

        notes = statistics.get("notes") or []

        if notes:
            st.subheader("Analysis notes")

            for note in notes:
                st.write(f"- {note}")
