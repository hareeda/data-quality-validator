
import os
import html

import pandas as pd
import requests
import streamlit as st


# ==================================================
# CONFIGURATION
# ==================================================

DEFAULT_API_URL = (
    "https://ai-data-quality-validator-api.onrender.com"
)

API_URL = os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")
MAX_FILE_SIZE = 10 * 1024 * 1024

st.set_page_config(
    page_title="Data Quality Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# PROFESSIONAL THEME AND RESPONSIVE LAYOUT
# ==================================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap'
    );

    :root {
        --navy: #172B4D;
        --teal: #0D9488;
        --muted: #64748B;
        --line: #E2E8F0;
        --background: #F6F8FB;
    }

    html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        max-width: 100%;
        overflow-x: hidden;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    .stApp {
        width: 100%;
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;
    }

    .stApp {
        background: var(--background);
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: clamp(1rem, 4vw, 3rem);
        padding-right: clamp(1rem, 4vw, 3rem);
        box-sizing: border-box;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid var(--line);
        flex-shrink: 0;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    /* Branding */

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.5rem;
        min-width: 0;
    }

    .brand-mark {
        background: var(--navy);
        color: #FFFFFF;
        width: 42px;
        height: 42px;
        min-width: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: 700;
    }

    .brand-name {
        font-size: 17px;
        font-weight: 700;
        color: var(--navy);
        line-height: 1.3;
        overflow-wrap: anywhere;
    }

    .brand-subtitle {
        color: var(--muted);
        font-size: 10px;
        margin-top: 3px;
        letter-spacing: 0.5px;
    }

    /* Page header */

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 11px;
        font-weight: 700;
        color: var(--teal);
        margin-bottom: 8px;
    }

    .page-title {
        color: var(--navy);
        font-size: clamp(27px, 3vw, 38px);
        font-weight: 700;
        line-height: 1.2;
        letter-spacing: -1px;
        margin: 0;
        overflow-wrap: anywhere;
    }

    .page-description {
        color: var(--muted);
        font-size: 15px;
        line-height: 1.7;
        margin-top: 10px;
        max-width: 760px;
        overflow-wrap: anywhere;
    }

    .section-heading {
        color: var(--navy);
        font-size: 20px;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 4px;
        overflow-wrap: anywhere;
    }

    .section-description {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
        margin-bottom: 18px;
    }

    /* Upload panel */

    .upload-panel {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 22px 24px;
        margin: 22px 0;
        box-sizing: border-box;
        max-width: 100%;
    }

    .upload-title {
        color: var(--navy);
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .upload-description {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
    }

    /* Status indicators */

    .status-pill {
        display: inline-block;
        border-radius: 20px;
        padding: 5px 11px;
        font-size: 12px;
        font-weight: 600;
        background: #E6F6F2;
        color: #087F70;
        max-width: 100%;
        overflow-wrap: anywhere;
    }

    .status-neutral {
        background: #EDF2F7;
        color: #475569;
    }

    .status-warning {
        background: #FFF4DB;
        color: #946200;
    }

    /* KPI cards */

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 18px 20px;
        min-height: 110px;
        box-sizing: border-box;
        min-width: 0;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: 13px;
        font-weight: 500;
    }

    div[data-testid="stMetricValue"] {
        color: var(--navy);
        font-size: clamp(20px, 2.5vw, 30px);
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    /* Tabs, tables and charts */

    div[data-testid="stTabs"] {
        max-width: 100%;
        min-width: 0;
    }

    div[data-testid="stTabs"] button {
        font-weight: 600;
        white-space: normal;
    }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"],
    div[data-testid="stVegaLiteChart"],
    div[data-testid="stPlotlyChart"],
    div[data-testid="stArrowVegaLiteChart"] {
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }

    div[data-testid="stFileUploader"] {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 8px;
        max-width: 100%;
        box-sizing: border-box;
    }

    /* Buttons */

    div.stButton > button {
        white-space: normal;
        overflow-wrap: anywhere;
        max-width: 100%;
        border-radius: 9px;
    }

    div.stButton > button[kind="primary"] {
        background: var(--navy);
        border: 1px solid var(--navy);
        font-weight: 600;
        min-height: 44px;
    }

    div.stButton > button[kind="primary"]:hover {
        background: var(--teal);
        border-color: var(--teal);
    }

    .stDownloadButton button {
        border-radius: 9px;
        font-weight: 600;
        white-space: normal;
    }

    /* Code blocks and long values */

    [data-testid="stCode"],
    [data-testid="stJson"] {
        max-width: 100%;
        min-width: 0;
        overflow-x: auto;
    }

    pre, code {
        overflow-wrap: anywhere;
    }

    /* Footer */

    .footer {
        border-top: 1px solid var(--line);
        margin-top: 42px;
        padding-top: 18px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.7;
        overflow-wrap: anywhere;
    }

    /* Smaller screens */

    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1rem;
        }

        .page-title {
            font-size: 28px;
            letter-spacing: -0.5px;
        }

        .upload-panel {
            padding: 16px;
        }

        div[data-testid="stMetric"] {
            padding: 12px;
            min-height: 95px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 21px;
        }
    }

    @media (max-width: 480px) {
        [data-testid="stMainBlockContainer"] {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }

        .page-title {
            font-size: 25px;
        }

        .section-heading {
            font-size: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# API FUNCTIONS
# ==================================================

def api_health():
    """Check the FastAPI service."""
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
    """Upload a CSV and retrieve its analysis."""
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
                detail = response.json().get(
                    "detail",
                    response.text,
                )
            except ValueError:
                detail = response.text

            return None, (
                f"API error ({response.status_code}): {detail}"
            )

        result = response.json()

        if not isinstance(result, dict):
            return None, "The API returned an unexpected response."

        if result.get("status") == "error":
            return None, result.get(
                "message",
                "The dataset could not be analyzed.",
            )

        return result, None

    except requests.Timeout:
        return None, (
            "The request timed out. The API may be starting up or "
            "processing your dataset. Please try again."
        )

    except requests.RequestException as exc:
        return None, f"Could not connect to the API: {exc}"

    except ValueError:
        return None, "The API returned an invalid JSON response."


# ==================================================
# DISPLAY HELPERS
# ==================================================

def section_header(title, description=None):
    """Render a consistent section heading."""
    st.markdown(
        f'<div class="section-heading">{html.escape(str(title))}</div>',
        unsafe_allow_html=True,
    )

    if description:
        st.markdown(
            '<div class="section-description">'
            f'{html.escape(str(description))}</div>',
            unsafe_allow_html=True,
        )


def format_number(value):
    """Format numeric values for display."""
    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass

    if isinstance(value, (int, float)):
        if isinstance(value, float):
            return f"{value:,.2f}"
        return f"{value:,}"

    return str(value)


def render_overview(summary):
    """Render the main KPI cards."""
    metrics = [
        ("Total records", summary.get("total_records", 0)),
        ("Columns", summary.get("total_columns", 0)),
        ("Quality findings", summary.get("total_issues", 0)),
        ("Affected records", summary.get("affected_records", 0)),
    ]

    columns = st.columns(4)

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, format_number(value))


def render_severity(summary):
    section_header(
        "Findings by severity",
        "Understand the distribution of detected data quality issues.",
    )

    severity = summary.get("issues_by_severity") or {}

    if not isinstance(severity, dict) or not severity:
        st.info("No severity findings are available.")
        return

    df = pd.DataFrame(
        [
            {"Severity": str(level), "Count": count}
            for level, count in severity.items()
        ]
    )

    st.bar_chart(df.set_index("Severity"), y="Count")


def render_rules(summary):
    section_header(
        "Validation rule breakdown",
        "See which quality checks generated the most findings.",
    )

    rules = summary.get("issues_by_rule") or {}

    if not isinstance(rules, dict) or not rules:
        st.info("No rule violations were recorded.")
        return

    df = pd.DataFrame(
        [
            {"Rule": str(rule), "Findings": count}
            for rule, count in rules.items()
        ]
    ).sort_values("Findings", ascending=False)

    st.bar_chart(df.set_index("Rule"), y="Findings")
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_dataset_overview(statistics):
    section_header(
        "Dataset statistics",
        "A snapshot of completeness, duplication, and storage footprint.",
    )

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


def normalize_top_values(values):
    """Normalize common top-values formats for display."""
    if values is None:
        return pd.DataFrame()

    if isinstance(values, dict):
        if not values:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {"Value": str(value), "Count": count}
                for value, count in values.items()
            ]
        )

    if isinstance(values, list):
        if not values:
            return pd.DataFrame()

        if all(isinstance(item, dict) for item in values):
            return pd.DataFrame(values)

        rows = []

        for item in values:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                rows.append(
                    {"Value": str(item[0]), "Count": item[1]}
                )
            else:
                rows.append({"Value": str(item)})

        return pd.DataFrame(rows)

    return pd.DataFrame({"Value": [str(values)]})


def render_column_profiles(statistics):
    section_header(
        "Column profiles",
        "Inspect data types, missing values, uniqueness, and numeric statistics.",
    )

    profiles = statistics.get("columns") or []

    if not profiles:
        st.info("No column profiles are available.")
        return

    valid_profiles = [
        profile
        for profile in profiles
        if isinstance(profile, dict)
    ]

    if not valid_profiles:
        st.info("No usable column profiles were returned.")
        return

    profile_rows = []

    for profile in valid_profiles:
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

        numeric = profile.get("statistics") or {}

        if isinstance(numeric, dict) and numeric:
            row.update({
                "Mean": numeric.get("mean"),
                "Median": numeric.get("median"),
                "Minimum": numeric.get("min"),
                "Maximum": numeric.get("max"),
                "Outliers (IQR)": numeric.get("outlier_count_iqr"),
            })

        dates = profile.get("date_statistics") or {}

        if isinstance(dates, dict) and dates:
            row["Earliest date"] = dates.get("min")
            row["Latest date"] = dates.get("max")

        profile_rows.append(row)

    st.dataframe(
        pd.DataFrame(profile_rows),
        use_container_width=True,
        hide_index=True,
    )

    available_profiles = [
        profile
        for profile in valid_profiles
        if profile.get("column") is not None
    ]

    if not available_profiles:
        return

    st.markdown("#### Explore an individual column")

    selected_column = st.selectbox(
        "Select a column",
        options=[profile["column"] for profile in available_profiles],
    )

    selected = next(
        (
            profile
            for profile in available_profiles
            if profile.get("column") == selected_column
        ),
        None,
    )

    if selected:
        with st.expander(
            f"Detailed profile — {selected_column}",
            expanded=True,
        ):
            st.json(selected)

            top_values_df = normalize_top_values(
                selected.get("top_values")
            )

            if not top_values_df.empty:
                st.markdown("#### Most frequent values")

                st.dataframe(
                    top_values_df,
                    use_container_width=True,
                    hide_index=True,
                )


def render_correlations(statistics):
    section_header(
        "Numeric correlations",
        "Explore relationships between numeric variables, when available.",
    )

    correlations = statistics.get("numeric_correlations") or {}

    if not isinstance(correlations, dict) or not correlations:
        st.info("No numeric correlations are available for this dataset.")
        return

    df = pd.DataFrame(correlations)

    if df.empty:
        st.info("No correlation data is available.")
        return

    st.dataframe(df, use_container_width=True)


def render_issues(issues):
    section_header(
        "Validation findings",
        "Filter and investigate individual data quality issues.",
    )

    if not issues:
        st.success(
            "No findings were detected by the current validation rules."
        )
        st.caption(
            "This does not guarantee that every value is correct "
            "or that all business rules have been checked."
        )
        return

    df = pd.DataFrame(issues)

    if df.empty:
        st.info("No detailed findings are available.")
        return

    filter_columns = st.columns(2)

    severity_options = (
        sorted(df["severity"].dropna().unique().tolist())
        if "severity" in df.columns
        else []
    )

    rule_options = (
        sorted(df["rule"].dropna().unique().tolist())
        if "rule" in df.columns
        else []
    )

    selected_severity = filter_columns[0].multiselect(
        "Severity",
        options=severity_options,
        default=severity_options,
    )

    selected_rules = filter_columns[1].multiselect(
        "Validation rule",
        options=rule_options,
        default=rule_options,
    )

    filtered = df.copy()

    if "severity" in filtered.columns:
        filtered = filtered[
            filtered["severity"].isin(selected_severity)
        ]

    if "rule" in filtered.columns:
        filtered = filtered[
            filtered["rule"].isin(selected_rules)
        ]

    st.caption(
        f"Displaying {len(filtered):,} of {len(df):,} findings."
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )


def render_report(report):
    section_header(
        "Quality assessment report",
        "Review the generated findings and recommended next steps.",
    )

    if not report:
        st.info("No report content was returned.")
        return

    st.markdown(report)

    st.download_button(
        label="Download report (.md)",
        data=report,
        file_name="data_quality_report.md",
        mime="text/markdown",
    )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">◈</div>
            <div>
                <div class="brand-name">Data Quality Studio</div>
                <div class="brand-subtitle">AI-POWERED ANALYTICS</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("**System status**")
    st.caption("Backend API")

    if st.button("Check connection", use_container_width=True):
        with st.spinner("Checking connection..."):
            healthy, details = api_health()

        if healthy:
            st.success("API connected")
            st.json(details)
        else:
            st.error("API unavailable")
            st.caption(str(details))

    st.divider()

    st.markdown("**Configuration**")
    st.caption("API endpoint")
    st.code(API_URL, language=None)
    st.caption("Maximum CSV size: 10 MB")

    st.divider()

    st.caption(
        "General-purpose data quality analysis for tabular datasets."
    )


# ==================================================
# MAIN PAGE HEADER
# ==================================================

st.markdown(
    '<div class="eyebrow">DATA INTELLIGENCE PLATFORM</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="page-title">Data Quality Overview</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-description">
        Assess dataset quality, uncover inconsistencies, explore statistical
        patterns, and generate actionable recommendations from your CSV data.
    </div>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# UPLOAD PANEL
# ==================================================

st.markdown(
    """
    <div class="upload-panel">
        <div class="upload-title">Analyze a dataset</div>
        <div class="upload-description">
            Upload a CSV file to run validation checks and statistical profiling.
            No fixed column names or company-specific schema are required.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Maximum supported file size is 10 MB.",
)

if uploaded_file is not None:
    st.caption(
        f"Selected file: {uploaded_file.name} · "
        f"{uploaded_file.size:,} bytes"
    )

    if uploaded_file.size == 0:
        st.error("The selected file is empty.")

    elif uploaded_file.size > MAX_FILE_SIZE:
        st.error("The maximum supported file size is 10 MB.")

    else:
        if st.button(
            "Run data quality analysis",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(
                "Analyzing the dataset. This may take a little while..."
            ):
                result, error = submit_csv(uploaded_file)

            if error:
                st.error(error)
            else:
                st.session_state["analysis_result"] = result
                st.session_state["analysis_filename"] = uploaded_file.name
                st.success("Analysis completed successfully.")


# ==================================================
# ANALYSIS RESULTS
# ==================================================

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]

    summary = result.get("summary") or {}
    statistics = summary.get("statistical_analysis") or {}
    issues = result.get("issues") or []
    report = result.get("report", "")
    evidence = result.get("evidence") or {}

    filename = st.session_state.get(
        "analysis_filename",
        result.get("dataset_name", "Dataset"),
    )

    st.divider()

    st.markdown(
        '<div class="eyebrow">ANALYSIS RESULTS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<h2 style="color:#172B4D; margin-top:0; '
        f'overflow-wrap:anywhere;">{html.escape(str(filename))}</h2>',
        unsafe_allow_html=True,
    )

    ai_status = result.get("ai_status", "unknown")

    if ai_status == "success":
        st.markdown(
            '<span class="status-pill">AI insights generated</span>',
            unsafe_allow_html=True,
        )

    elif ai_status == "fallback":
        st.markdown(
            '<span class="status-pill status-warning">'
            'Rule-based report displayed</span>',
            unsafe_allow_html=True,
        )

        st.caption(
            "AI insights were unavailable; validation results remain available."
        )

    else:
        st.markdown(
            '<span class="status-pill status-neutral">'
            f'Insight status: {html.escape(str(ai_status))}</span>',
            unsafe_allow_html=True,
        )

    st.write("")

    render_overview(summary)

    tabs = st.tabs([
        "Overview",
        "Column profiles",
        "Validation findings",
        "AI report",
        "Evidence",
    ])

    with tabs[0]:
        render_severity(summary)
        st.divider()
        render_rules(summary)
        st.divider()
        render_dataset_overview(statistics)

    with tabs[1]:
        render_column_profiles(statistics)
        st.divider()
        render_correlations(statistics)

    with tabs[2]:
        render_issues(issues)

    with tabs[3]:
        render_report(report)

    with tabs[4]:
        section_header(
            "Analysis evidence",
            "Supporting summary used to produce the quality assessment.",
        )

        st.json(evidence)

        notes = statistics.get("notes") or []

        if notes:
            st.markdown("#### Statistical analysis notes")

            for note in notes:
                st.write(f"- {note}")

else:
    st.info(
        "Upload a CSV file above and run an analysis to view your results here."
    )


# ==================================================
# FOOTER
# ==================================================

st.markdown(
    """
    <div class="footer">
        <strong>Data Quality Studio</strong> · AI-powered data quality analysis
        <br>
        Findings are based on configured validation rules and statistical
        checks. Review unusual values in the context of your dataset before
        treating them as errors.
    </div>
    """,
    unsafe_allow_html=True,
)
