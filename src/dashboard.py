import os
import html

import altair as alt
import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_API_URL = "https://ai-data-quality-validator-api.onrender.com"
API_URL = os.getenv("API_URL", DEFAULT_API_URL).rstrip("/")
MAX_FILE_SIZE = 10 * 1024 * 1024

st.set_page_config(
    page_title="Data Quality Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    :root {
        --navy: #14243A;
        --navy-soft: #203852;
        --teal: #0F9D91;
        --teal-light: #E7F7F4;
        --ink: #172B4D;
        --muted: #68778D;
        --line: #E4EAF1;
        --canvas: #F5F7FA;
        --white: #FFFFFF;
    }

    html, body { margin: 0; width: 100%; max-width: 100%; overflow-x: hidden; }
    .stApp { background: var(--canvas); font-family: 'DM Sans', sans-serif; }
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        width: 100%; max-width: 100%; min-width: 0; box-sizing: border-box;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1480px; padding: 2rem clamp(1rem, 3.5vw, 3rem) 3rem;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: var(--navy); border-right: 0; flex-shrink: 0;
    }
    [data-testid="stSidebar"] > div:first-child { background: var(--navy); }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span { color: #D9E3EE; }
    [data-testid="stSidebar"] hr { border-color: #34475E; }
    [data-testid="stSidebar"] .stCode, [data-testid="stSidebar"] code {
        color: #D9E3EE !important; background: #20344B !important;
    }
    [data-testid="stSidebar"] button {
        border-color: #40536A; color: #FFFFFF; background: #20344B;
    }
    [data-testid="stSidebar"] button:hover { border-color: var(--teal); }

    .brand { display:flex; align-items:center; gap:12px; margin: .25rem 0 1.6rem; }
    .brand-mark {
        display:flex; align-items:center; justify-content:center;
        width:42px; height:42px; min-width:42px; border-radius:12px;
        color:white; background:var(--teal); font-size:24px; font-weight:700;
    }
    .brand-name { color:#FFFFFF; font-size:16px; font-weight:700; line-height:1.25; }
    .brand-subtitle { color:#AAB9C9; font-size:10px; letter-spacing:1.3px; margin-top:5px; }
    .side-label { color:#8EA2B8; text-transform:uppercase; letter-spacing:1.3px;
        font-size:10px; font-weight:700; margin:1.25rem 0 .45rem; }
    .side-note { color:#AAB9C9; font-size:12px; line-height:1.7; }

    .eyebrow { color:var(--teal); text-transform:uppercase; letter-spacing:1.7px;
        font-size:10px; font-weight:700; margin-bottom:8px; }
    .page-title { color:var(--ink); font-size:clamp(28px, 3vw, 38px);
        font-weight:700; letter-spacing:-1px; line-height:1.18; margin:0; overflow-wrap:anywhere; }
    .page-description { color:var(--muted); font-size:14px; line-height:1.7;
        margin-top:10px; max-width:800px; }
    .page-topline { display:flex; align-items:center; justify-content:space-between;
        gap:1rem; flex-wrap:wrap; margin-bottom:1.8rem; }
    .top-badge { display:inline-block; background:#E7F7F4; color:#087F73;
        border:1px solid #CDEDE7; padding:7px 11px; border-radius:999px;
        font-size:11px; font-weight:700; letter-spacing:.3px; }

    .panel {
        background:#FFFFFF; border:1px solid var(--line); border-radius:16px;
        padding:22px 24px; box-shadow:0 2px 8px rgba(20,36,58,.025);
        box-sizing:border-box; max-width:100%;
    }
    .panel-title { color:var(--ink); font-size:17px; font-weight:700; margin-bottom:5px; }
    .panel-copy { color:var(--muted); font-size:13px; line-height:1.65; }
    .section-heading { color:var(--ink); font-size:20px; font-weight:700;
        margin:10px 0 4px; overflow-wrap:anywhere; }
    .section-description { color:var(--muted); font-size:13px; line-height:1.6; margin-bottom:16px; }
    .status-pill { display:inline-block; border-radius:999px; padding:5px 10px;
        font-size:11px; font-weight:700; background:#E7F7F4; color:#087F73; }
    .status-warning { background:#FFF4D9; color:#946200; }
    .status-neutral { background:#EDF2F7; color:#475569; }

    div[data-testid="stMetric"] {
        background:#FFFFFF; border:1px solid var(--line); border-radius:14px;
        padding:18px 19px; min-height:112px; min-width:0; box-sizing:border-box;
        box-shadow:0 2px 8px rgba(20,36,58,.025);
    }
    div[data-testid="stMetricLabel"] { color:var(--muted); font-size:12px; font-weight:600; }
    div[data-testid="stMetricValue"] { color:var(--ink); font-size:clamp(21px, 2.2vw, 30px);
        font-weight:700; overflow-wrap:anywhere; }
    div[data-testid="stMetricDelta"] { font-size:11px; }

    div[data-testid="stTabs"] { max-width:100%; min-width:0; }
    div[data-testid="stTabs"] button { font-weight:600; font-size:13px; white-space:normal; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color:var(--teal); }
    div[data-testid="stDataFrame"], div[data-testid="stTable"],
    div[data-testid="stVegaLiteChart"], div[data-testid="stPlotlyChart"],
    div[data-testid="stArrowVegaLiteChart"], [data-testid="stJson"] {
        max-width:100%; min-width:0; box-sizing:border-box;
    }
    div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
    div[data-testid="stFileUploader"] {
        background:#FFFFFF; border:1px dashed #B8C7D8; border-radius:12px;
        padding:10px; max-width:100%; box-sizing:border-box;
    }
    div.stButton > button, .stDownloadButton button {
        border-radius:9px; font-weight:600; white-space:normal; max-width:100%;
    }
    div.stButton > button[kind="primary"] {
        background:var(--navy); border:1px solid var(--navy); min-height:44px;
    }
    div.stButton > button[kind="primary"]:hover {
        background:var(--teal); border-color:var(--teal);
    }
    .footer { border-top:1px solid var(--line); margin-top:42px; padding-top:18px;
        color:var(--muted); font-size:12px; line-height:1.7; overflow-wrap:anywhere; }
    @media (max-width:768px) {
        [data-testid="stMainBlockContainer"] { padding:1rem; }
        .page-title { font-size:27px; letter-spacing:-.5px; }
        .panel { padding:16px; }
        div[data-testid="stMetric"] { padding:12px; min-height:96px; }
        div[data-testid="stMetricValue"] { font-size:21px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API
# ============================================================

def api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=60)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as exc:
        return False, str(exc)
    except ValueError as exc:
        return False, f"Invalid health response: {exc}"


def submit_csv(uploaded_file):
    try:
        response = requests.post(
            f"{API_URL}/upload-csv",
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
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
            return None, "The API returned an unexpected response."
        if result.get("status") == "error":
            return None, result.get("message", "The dataset could not be analyzed.")
        return result, None
    except requests.Timeout:
        return None, "The request timed out. The API may be starting or processing the dataset. Please try again."
    except requests.RequestException as exc:
        return None, f"Could not connect to the API: {exc}"
    except ValueError:
        return None, "The API returned an invalid JSON response."


# ============================================================
# DISPLAY HELPERS
# ============================================================

def section_header(title, description=None):
    st.markdown(
        f'<div class="section-heading">{html.escape(str(title))}</div>',
        unsafe_allow_html=True,
    )
    if description:
        st.markdown(
            f'<div class="section-description">{html.escape(str(description))}</div>',
            unsafe_allow_html=True,
        )


def format_number(value):
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


def render_overview(summary):
    metrics = [
        ("Total records", summary.get("total_records", 0)),
        ("Columns", summary.get("total_columns", 0)),
        ("Quality findings", summary.get("total_issues", 0)),
        ("Affected records", summary.get("affected_records", 0)),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, format_number(value))


def render_severity(summary):
    section_header("Findings by severity", "Understand the distribution of detected data quality issues.")
    severity = summary.get("issues_by_severity") or {}
    if not isinstance(severity, dict) or not severity:
        st.info("No severity findings are available.")
        return
    df = pd.DataFrame([{"Severity": str(level), "Count": count} for level, count in severity.items()])
    st.bar_chart(df.set_index("Severity"), y="Count")


def render_rules(summary):
    section_header("Validation rule breakdown", "See which quality checks generated the most findings.")
    rules = summary.get("issues_by_rule") or {}
    if not isinstance(rules, dict) or not rules:
        st.info("No rule violations were recorded.")
        return
    df = pd.DataFrame([{"Rule": str(rule), "Findings": count} for rule, count in rules.items()])
    df = df.sort_values("Findings", ascending=False)
    st.bar_chart(df.set_index("Rule"), y="Findings")
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_insight_charts(summary, statistics):
    """Render charts only when the returned data supports meaningful comparisons."""
    section_header(
        "Visual insights",
        "Charts are generated from the actual validation and profiling results.",
    )

    severity = summary.get("issues_by_severity") or {}
    overview = statistics.get("dataset_overview") or {}

    left, right = st.columns(2)

    with left:
        st.markdown("**Findings by severity**")
        if isinstance(severity, dict):
            severity_rows = [
                {"Severity": str(level).title(), "Findings": int(count)}
                for level, count in severity.items()
                if isinstance(count, (int, float)) and count > 0
            ]
        else:
            severity_rows = []

        if severity_rows:
            severity_df = pd.DataFrame(severity_rows)
            pie = (
                alt.Chart(severity_df)
                .mark_arc(outerRadius=105, innerRadius=52)
                .encode(
                    theta=alt.Theta("Findings:Q", stack=True),
                    color=alt.Color(
                        "Severity:N",
                        title="Severity",
                        scale=alt.Scale(
                            domain=["High", "Medium", "Low"],
                            range=["#D9485F", "#E9A23B", "#0F9D91"],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Severity:N"),
                        alt.Tooltip("Findings:Q", format=","),
                    ],
                )
                .properties(height=250)
            )
            st.altair_chart(pie, use_container_width=True)
            total = sum(row["Findings"] for row in severity_rows)
            st.caption(f"{total:,} findings across {len(severity_rows)} severity categories.")
        else:
            st.info("A severity pie chart will appear when validation findings are present.")

    with right:
        st.markdown("**Dataset completeness**")
        try:
            total_cells = int(overview.get("total_cells", 0) or 0)
            missing_cells = int(overview.get("total_missing_cells", 0) or 0)
        except (TypeError, ValueError):
            total_cells, missing_cells = 0, 0

        if total_cells > 0:
            present_cells = max(total_cells - missing_cells, 0)
            completeness_df = pd.DataFrame([
                {"Cell status": "Populated", "Cells": present_cells},
                {"Cell status": "Missing", "Cells": missing_cells},
            ])
            completeness_chart = (
                alt.Chart(completeness_df)
                .mark_arc(outerRadius=105, innerRadius=52)
                .encode(
                    theta=alt.Theta("Cells:Q", stack=True),
                    color=alt.Color(
                        "Cell status:N",
                        title="Cell status",
                        scale=alt.Scale(
                            domain=["Populated", "Missing"],
                            range=["#0F9D91", "#D9485F"],
                        ),
                    ),
                    tooltip=[
                        alt.Tooltip("Cell status:N"),
                        alt.Tooltip("Cells:Q", format=","),
                    ],
                )
                .properties(height=250)
            )
            st.altair_chart(completeness_chart, use_container_width=True)
            completeness = (present_cells / total_cells) * 100
            st.caption(
                f"{completeness:.1f}% populated · "
                f"{missing_cells:,} missing cells out of {total_cells:,} total cells."
            )
        else:
            st.info("Completeness chart unavailable because total cell count is zero or missing.")


def render_missingness_chart(statistics):
    """Show missing-value percentage by column, when column profiles are available."""
    profiles = statistics.get("columns") or []
    rows = []

    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        column_name = profile.get("column")
        missing_percent = profile.get("missing_percent", 0)
        try:
            missing_percent = float(missing_percent or 0)
        except (TypeError, ValueError):
            continue

        if column_name is not None:
            rows.append({
                "Column": str(column_name),
                "Missing %": max(0, min(100, missing_percent)),
                "Missing cells": profile.get("missing_count", 0),
            })

    if not rows:
        st.info("Column-level missingness data is not available.")
        return

    df = pd.DataFrame(rows).sort_values("Missing %", ascending=False)
    df = df[df["Missing %"] > 0].head(15)

    if df.empty:
        st.success("No missing values were detected in the profiled columns.")
        return

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, color="#0F9D91")
        .encode(
            x=alt.X("Missing %:Q", title="Missing values (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Column:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("Column:N"),
                alt.Tooltip("Missing %:Q", format=".2f"),
                alt.Tooltip("Missing cells:Q", format=","),
            ],
        )
        .properties(height=max(180, 28 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Showing up to 15 columns with the highest missing-value percentages.")


def render_numeric_distributions(statistics):
    """Show a compact numeric profile chart when numeric columns exist."""
    profiles = statistics.get("columns") or []
    numeric_rows = []

    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        numeric = profile.get("statistics") or {}
        if not isinstance(numeric, dict):
            continue

        mean = numeric.get("mean")
        median = numeric.get("median")
        if mean is None and median is None:
            continue

        try:
            if mean is not None:
                mean = float(mean)
            if median is not None:
                median = float(median)
        except (TypeError, ValueError):
            continue

        numeric_rows.append({
            "Column": str(profile.get("column", "Column")),
            "Mean": mean,
            "Median": median,
        })

    if not numeric_rows:
        st.info("No numeric column statistics are available for comparison.")
        return

    df = pd.DataFrame(numeric_rows)
    long_df = df.melt(
        id_vars=["Column"],
        value_vars=["Mean", "Median"],
        var_name="Statistic",
        value_name="Value",
    ).dropna(subset=["Value"])

    chart = (
        alt.Chart(long_df)
        .mark_bar()
        .encode(
            x=alt.X("Value:Q", title="Value"),
            y=alt.Y("Column:N", sort="-x", title=None),
            color=alt.Color(
                "Statistic:N",
                title="Statistic",
                scale=alt.Scale(
                    domain=["Mean", "Median"],
                    range=["#203852", "#0F9D91"],
                ),
            ),
            yOffset="Statistic:N",
            tooltip=[
                alt.Tooltip("Column:N"),
                alt.Tooltip("Statistic:N"),
                alt.Tooltip("Value:Q", format=",.3f"),
            ],
        )
        .properties(height=max(180, 32 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(
        "Mean and median are shown for numeric columns. Compare columns "
        "with similar units or scales for the most meaningful interpretation."
    )


def render_issue_rule_chart(summary):
    """Show the most common validation rules as a horizontal bar chart."""
    rules = summary.get("issues_by_rule") or {}
    if not isinstance(rules, dict) or not rules:
        st.info("No rule-frequency data is available.")
        return

    rows = []
    for rule, count in rules.items():
        try:
            numeric_count = int(count)
        except (TypeError, ValueError):
            continue
        if numeric_count > 0:
            rows.append({"Rule": str(rule), "Findings": numeric_count})

    if not rows:
        st.info("No validation-rule findings were recorded.")
        return

    df = pd.DataFrame(rows).sort_values("Findings", ascending=False).head(10)
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, color="#203852")
        .encode(
            x=alt.X("Findings:Q", title="Number of findings"),
            y=alt.Y("Rule:N", sort="-x", title=None),
            tooltip=["Rule:N", alt.Tooltip("Findings:Q", format=",")],
        )
        .properties(height=max(180, 30 * len(df)))
    )
    st.altair_chart(chart, use_container_width=True)


def render_dataset_overview(statistics):
    section_header("Dataset statistics", "A snapshot of completeness, duplication, and storage footprint.")
    overview = statistics.get("dataset_overview") or {}
    metrics = [
        ("Duplicate rows", overview.get("duplicate_row_count", 0)),
        ("Missing cells", overview.get("total_missing_cells", 0)),
        ("Total cells", overview.get("total_cells", 0)),
        ("Memory usage", f"{format_number(overview.get('memory_usage_bytes', 0))} bytes"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def normalize_top_values(values):
    if values is None:
        return pd.DataFrame()
    if isinstance(values, dict):
        return pd.DataFrame([{"Value": str(value), "Count": count} for value, count in values.items()])
    if isinstance(values, list):
        if not values:
            return pd.DataFrame()
        if all(isinstance(item, dict) for item in values):
            return pd.DataFrame(values)
        rows = []
        for item in values:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                rows.append({"Value": str(item[0]), "Count": item[1]})
            else:
                rows.append({"Value": str(item)})
        return pd.DataFrame(rows)
    return pd.DataFrame({"Value": [str(values)]})


def render_column_profiles(statistics):
    section_header("Column profiles", "Inspect data types, missing values, uniqueness, and numeric statistics.")
    profiles = statistics.get("columns") or []
    valid_profiles = [p for p in profiles if isinstance(p, dict)]
    if not valid_profiles:
        st.info("No column profiles are available.")
        return

    rows = []
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
        rows.append(row)

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    options = [p.get("column") for p in valid_profiles if p.get("column") is not None]
    if not options:
        return
    selected_column = st.selectbox("Explore an individual column", options=options)
    selected = next((p for p in valid_profiles if p.get("column") == selected_column), None)
    if selected:
        with st.expander(f"Detailed profile — {selected_column}", expanded=False):
            st.json(selected)
            top_df = normalize_top_values(selected.get("top_values"))
            if not top_df.empty:
                st.markdown("**Most frequent values**")
                st.dataframe(top_df, use_container_width=True, hide_index=True)


def render_correlations(statistics):
    section_header("Numeric correlations", "Explore relationships between numeric variables, when available.")
    correlations = statistics.get("numeric_correlations") or {}
    if not isinstance(correlations, dict) or not correlations:
        st.info("No numeric correlations are available for this dataset.")
        return
    df = pd.DataFrame(correlations)
    if df.empty:
        st.info("No correlation data is available.")
    else:
        st.dataframe(df, use_container_width=True)


def render_issues(issues):
    section_header("Validation findings", "Filter and investigate individual data quality issues.")
    if not issues:
        st.success("No findings were detected by the current validation rules.")
        st.caption("This does not guarantee that every value is correct or that all business rules have been checked.")
        return

    df = pd.DataFrame(issues)
    if df.empty:
        st.info("No detailed findings are available.")
        return

    c1, c2 = st.columns(2)
    severity_options = sorted(df["severity"].dropna().unique().tolist()) if "severity" in df.columns else []
    rule_options = sorted(df["rule"].dropna().unique().tolist()) if "rule" in df.columns else []
    chosen_severity = c1.multiselect("Severity", severity_options, default=severity_options)
    chosen_rules = c2.multiselect("Validation rule", rule_options, default=rule_options)

    filtered = df.copy()
    if "severity" in filtered.columns:
        filtered = filtered[filtered["severity"].isin(chosen_severity)]
    if "rule" in filtered.columns:
        filtered = filtered[filtered["rule"].isin(chosen_rules)]

    st.caption(f"Displaying {len(filtered):,} of {len(df):,} findings.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)


def render_report(report):
    section_header("Quality assessment report", "Review the generated findings and recommended next steps.")
    if not report:
        st.info("No report content was returned.")
        return
    st.markdown(report)
    st.download_button(
        "Download report (.md)",
        data=report,
        file_name="data_quality_report.md",
        mime="text/markdown",
    )


# ============================================================
# SIDEBAR
# ============================================================

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
    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-note">Upload and profile any tabular CSV dataset. Review quality findings and generate a shareable report.</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div class="side-label">System status</div>', unsafe_allow_html=True)
    if st.button("Check API connection", use_container_width=True):
        with st.spinner("Checking API..."):
            healthy, details = api_health()
        if healthy:
            st.success("API connected")
            st.json(details)
        else:
            st.error("API unavailable")
            st.caption(str(details))
    st.markdown('<div class="side-label">Configuration</div>', unsafe_allow_html=True)
    st.caption("API endpoint")
    st.code(API_URL, language=None)
    st.caption("Maximum CSV size: 10 MB")


# ============================================================
# PAGE HEADER AND UPLOAD
# ============================================================

st.markdown(
    """
    <div class="page-topline">
        <div>
            <div class="eyebrow">DATA INTELLIGENCE PLATFORM</div>
            <h1 class="page-title">Data Quality Overview</h1>
            <div class="page-description">
                Understand your data health, uncover inconsistencies, explore
                statistical patterns, and turn findings into actionable next steps.
            </div>
        </div>
        <div class="top-badge">● &nbsp; ANALYTICS WORKSPACE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="panel">
        <div class="panel-title">Analyze a dataset</div>
        <div class="panel-copy">
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
    st.caption(f"Selected file: {uploaded_file.name} · {uploaded_file.size:,} bytes")
    if uploaded_file.size == 0:
        st.error("The selected file is empty.")
    elif uploaded_file.size > MAX_FILE_SIZE:
        st.error("The maximum supported file size is 10 MB.")
    elif st.button("Run data quality analysis", type="primary", use_container_width=True):
        with st.spinner("Analyzing the dataset. This may take a little while..."):
            result, error = submit_csv(uploaded_file)
        if error:
            st.error(error)
        else:
            st.session_state["analysis_result"] = result
            st.session_state["analysis_filename"] = uploaded_file.name
            st.success("Analysis completed successfully.")


# ============================================================
# RESULTS
# ============================================================

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]
    summary = result.get("summary") or {}
    statistics = summary.get("statistical_analysis") or {}
    issues = result.get("issues") or []
    report = result.get("report", "")
    evidence = result.get("evidence") or {}
    filename = st.session_state.get("analysis_filename", result.get("dataset_name", "Dataset"))
    ai_status = result.get("ai_status", "unknown")

    st.write("")
    st.markdown('<div class="eyebrow">ANALYSIS RESULTS</div>', unsafe_allow_html=True)
    st.markdown(
        f'<h2 style="color:#172B4D; margin:0 0 10px; overflow-wrap:anywhere;">{html.escape(str(filename))}</h2>',
        unsafe_allow_html=True,
    )

    if ai_status == "success":
        st.markdown('<span class="status-pill">AI insights generated</span>', unsafe_allow_html=True)
    elif ai_status == "fallback":
        st.markdown('<span class="status-pill status-warning">Rule-based report displayed</span>', unsafe_allow_html=True)
        st.caption("AI insights were unavailable; validation results remain available.")
    else:
        st.markdown(
            f'<span class="status-pill status-neutral">Insight status: {html.escape(str(ai_status))}</span>',
            unsafe_allow_html=True,
        )

    st.write("")
    render_overview(summary)

    tabs = st.tabs(["Overview", "Column profiles", "Validation findings", "AI report", "Evidence"])

    with tabs[0]:
        render_insight_charts(summary, statistics)
        st.divider()
        section_header(
            "Missing-value hotspots",
            "Quickly identify columns that may need cleaning or investigation.",
        )
        render_missingness_chart(statistics)
        st.divider()
        section_header(
            "Numeric profile comparison",
            "Compare mean and median values for numeric columns where available.",
        )
        render_numeric_distributions(statistics)
        st.divider()
        render_severity(summary)
        st.divider()
        render_rules(summary)
        st.divider()
        section_header(
            "Most frequent issue types",
            "Focus first on validation rules producing the largest number of findings.",
        )
        render_issue_rule_chart(summary)
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
        section_header("Analysis evidence", "Supporting summary used to produce the quality assessment.")
        if evidence:
            st.json(evidence)
        else:
            st.info("No separate evidence summary was returned.")
        notes = statistics.get("notes") or []
        if notes:
            st.markdown("**Statistical analysis notes**")
            for note in notes:
                st.write(f"- {note}")
else:
    st.markdown(
        """
        <div class="panel" style="margin-top:20px;">
            <div class="panel-title">Your analysis will appear here</div>
            <div class="panel-copy">
                Upload a CSV above to view dataset metrics, column-level statistics,
                validation findings, and the generated quality report.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        <strong>Data Quality Studio</strong> · AI-powered data quality analysis<br>
        Findings are based on configured validation rules and statistical checks.
        Review unusual values in the context of your dataset before treating them as errors.
    </div>
    """,
    unsafe_allow_html=True,
)
