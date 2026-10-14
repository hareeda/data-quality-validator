
import json

import pandas as pd
import requests
import streamlit as st


DEFAULT_API_URL = "https://ai-data-quality-validator-api.onrender.com"
REQUEST_TIMEOUT = 300
MAX_FILE_SIZE = 10 * 1024 * 1024


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Data Quality Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1450px;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.07);
            border: 1px solid rgba(128, 128, 128, 0.18);
            padding: 16px;
            border-radius: 12px;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.9rem;
        }

        div[data-testid="stFileUploader"] {
            border-radius: 12px;
        }

        .section-intro {
            color: #737783;
            font-size: 0.95rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "api_url" not in st.session_state:
    st.session_state["api_url"] = DEFAULT_API_URL

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "analysis_filename" not in st.session_state:
    st.session_state["analysis_filename"] = None


# --------------------------------------------------
# Header and help guide
# --------------------------------------------------

header_col, help_col = st.columns([5, 1])

with header_col:
    st.title("📊 Data Quality Intelligence")
    st.caption(
        "Understand your data. Detect quality risks. Discover insights."
    )

with help_col:
    with st.popover("❔ Help & Guide", use_container_width=True):
        st.subheader("Welcome to Data Quality Intelligence")

        st.write(
            "This application analyzes a CSV dataset, identifies potential "
            "data quality issues, calculates descriptive statistics, and "
            "presents evidence and AI-assisted business insights."
        )

        st.divider()
        st.markdown("### 1. Upload a dataset")
        st.write(
            "Choose a CSV file using the upload area on the main screen. "
            "The current backend expects company data with the required "
            "columns. Files must be no larger than 10 MB."
        )

        st.markdown("### 2. Run the analysis")
        st.write(
            "Click **Analyze dataset**. The backend runs validation rules, "
            "calculates dataset statistics, prepares evidence, and attempts "
            "to generate business insights."
        )

        st.markdown("### 3. Understand the overview")
        st.write(
            "- **Records analyzed:** number of records processed.\n"
            "- **Validation findings:** total rule-generated findings.\n"
            "- **Affected records:** distinct records flagged by validation.\n"
            "- **High-severity findings:** findings classified as HIGH."
        )

        st.markdown("### 4. Explore statistical analysis")
        st.write(
            "- **Dataset statistics:** rows, columns, missing cells, and duplicates.\n"
            "- **Column profiles:** data types, missing percentages, unique values, "
            "and descriptive statistics.\n"
            "- **Categorical distributions:** common values in categorical fields.\n"
            "- **Correlation matrix:** associations between eligible numeric columns.\n"
            "- **Statistical notes:** guidance on interpreting the results."
        )

        st.markdown("### 5. Review validation findings")
        st.write(
            "Explore findings by severity and validation rule. Use the filters "
            "and search box to narrow the results. Findings are flags that may "
            "need investigation; they are not automatically confirmed errors."
        )

        st.markdown("### 6. Review evidence and AI insights")
        st.write(
            "Open the rule-level evidence sections to inspect examples. "
            "Review the business quality report for explanations and suggested "
            "actions. Treat AI-generated recommendations as suggestions for "
            "human review."
        )

        st.markdown("### 7. Download your results")
        st.write(
            "Download filtered findings as CSV, the business quality report "
            "as Markdown, or the structured analysis results as JSON."
        )

        st.divider()
        st.markdown("### Advanced settings")

        st.text_input(
            "Backend API URL",
            key="api_url",
            help="Change this only if your backend is hosted at another URL.",
        )

        if st.button("Clear current analysis", use_container_width=True):
            st.session_state["analysis_result"] = None
            st.session_state["analysis_filename"] = None
            st.rerun()


st.divider()


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def get_statistical_analysis(result, summary):
    """Support both known API response formats."""
    statistical = summary.get("statistical_analysis")

    if not statistical:
        statistical = result.get("statistical_analysis")

    return statistical if isinstance(statistical, dict) else {}


def safe_number(value, default=0):
    """Return a safe value for metrics."""
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
        return value
    except (TypeError, ValueError):
        return default


# --------------------------------------------------
# Backend connection status
# --------------------------------------------------

api_url = st.session_state["api_url"].strip().rstrip("/")

status_col, status_description_col = st.columns([1, 4])

api_healthy = False

try:
    health_response = requests.get(
        f"{api_url}/health",
        timeout=10,
    )
    api_healthy = health_response.ok
except requests.RequestException:
    api_healthy = False

with status_col:
    if api_healthy:
        st.success("Backend connected")
    else:
        st.error("Backend unavailable")

with status_description_col:
    st.caption(
        "Upload a CSV to run validation and statistical analysis. "
        "Use **Help & Guide** above whenever you need navigation instructions."
    )


# --------------------------------------------------
# Upload section
# --------------------------------------------------

st.subheader("Analyze your dataset")

st.markdown(
    '<p class="section-intro">'
    "Upload your company dataset to identify quality issues and explore "
    "statistical patterns."
    "</p>",
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
    help="Maximum file size: 10 MB.",
)

if uploaded_file is not None:
    st.caption(f"Selected file: **{uploaded_file.name}**")

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("The selected file exceeds the 10 MB limit.")

    elif st.button(
        "🔍 Analyze dataset",
        type="primary",
        use_container_width=False,
        disabled=not api_healthy,
    ):
        try:
            with st.spinner(
                "Validating data, calculating statistics, "
                "and generating insights..."
            ):
                response = requests.post(
                    f"{api_url}/upload-csv",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "text/csv",
                        )
                    },
                    timeout=REQUEST_TIMEOUT,
                )

            if response.ok:
                response_data = response.json()

                st.session_state["analysis_result"] = response_data
                st.session_state["analysis_filename"] = uploaded_file.name

                st.success("Analysis completed successfully.")

            else:
                try:
                    detail = response.json().get(
                        "detail",
                        response.text,
                    )
                except ValueError:
                    detail = response.text

                st.error(
                    f"Request failed ({response.status_code}): {detail}"
                )

        except requests.Timeout:
            st.error(
                "The analysis took too long. Check the backend logs "
                "and try again."
            )

        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")

        except ValueError as exc:
            st.error(f"The backend returned an invalid response: {exc}")


# --------------------------------------------------
# Results
# --------------------------------------------------

result = st.session_state.get("analysis_result")

if result:
    summary = result.get("summary") or {}
    issues = result.get("issues") or []
    report = result.get("report") or ""
    evidence = result.get("evidence") or {}
    ai_status = result.get("ai_status", "unknown")

    statistical = get_statistical_analysis(result, summary)

    st.divider()
    st.header("Analysis results")

    filename = st.session_state.get(
        "analysis_filename",
        "Uploaded dataset",
    )
    st.caption(f"Dataset: **{filename}**")

    # ----------------------------------------------
    # AI status
    # ----------------------------------------------

    st.markdown("### AI insight generation")

    if ai_status == "success":
        st.success("The AI service successfully returned a report.")
    elif ai_status == "fallback":
        st.warning(
            "A fallback report was generated because AI insight generation "
            "was unavailable."
        )
    else:
        st.info(
            "The backend did not specify whether AI or fallback logic "
            "generated the report."
        )

    # ----------------------------------------------
    # KPI metrics
    # ----------------------------------------------

    st.markdown("### Dataset overview")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric(
            "Records analyzed",
            safe_number(summary.get("total_records")),
        )

    with k2:
        st.metric(
            "Validation findings",
            safe_number(summary.get("total_issues")),
        )

    with k3:
        st.metric(
            "Affected records",
            safe_number(summary.get("affected_records")),
        )

    severity_counts = summary.get("issues_by_severity") or {}
    rule_counts = summary.get("issues_by_rule") or {}

    with k4:
        st.metric(
            "High-severity findings",
            safe_number(severity_counts.get("HIGH")),
        )

    # ----------------------------------------------
    # Statistical analysis
    # ----------------------------------------------

    st.divider()
    st.header("Statistical analysis")

    if statistical:
        overview = statistical.get("dataset_overview") or {}

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.metric(
                "Rows",
                safe_number(overview.get("row_count")),
            )

        with stat_col2:
            st.metric(
                "Columns",
                safe_number(overview.get("column_count")),
            )

        with stat_col3:
            st.metric(
                "Missing cells",
                safe_number(overview.get("total_missing_cells")),
            )

        with stat_col4:
            st.metric(
                "Duplicate rows",
                safe_number(overview.get("duplicate_row_count")),
            )

        total_cells = safe_number(overview.get("total_cells"))
        memory_bytes = safe_number(overview.get("memory_usage_bytes"))

        st.caption(
            f"Total cells: {total_cells:,} | "
            f"Memory usage: {memory_bytes:,} bytes"
        )

        # Column profiles
        column_profiles = statistical.get("columns") or []

        st.markdown("### Column profiles")

        if column_profiles:
            profile_rows = []

            for column in column_profiles:
                stats = column.get("statistics") or {}
                date_stats = column.get("date_statistics") or {}

                profile_rows.append(
                    {
                        "Column": column.get("column"),
                        "Data type": column.get("data_type"),
                        "Profile type": column.get("profile_type"),
                        "Non-missing": column.get("non_missing_count"),
                        "Missing": column.get("missing_count"),
                        "Missing (%)": column.get("missing_percent"),
                        "Unique values": column.get("unique_count"),
                        "Unique (%)": column.get("unique_percent"),
                        "Mean": stats.get("mean"),
                        "Median": stats.get("median"),
                        "Standard deviation": stats.get("standard_deviation"),
                        "Minimum": stats.get("minimum"),
                        "Maximum": stats.get("maximum"),
                        "IQR outliers": stats.get("outlier_count_iqr"),
                        "Earliest date": date_stats.get("earliest"),
                        "Latest date": date_stats.get("latest"),
                    }
                )

            st.dataframe(
                pd.DataFrame(profile_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No column profiles were returned by the backend.")

        # Categorical distributions
        categorical_columns = [
            column
            for column in column_profiles
            if column.get("profile_type") == "categorical"
        ]

        if categorical_columns:
            st.markdown("### Categorical distributions")

            for column in categorical_columns:
                name = column.get("column", "Unknown column")

                with st.expander(f"Explore {name}"):
                    st.write(
                        f"Distinct categories: "
                        f"{column.get('category_count', 0)}"
                    )
                    st.write(
                        f"High cardinality: "
                        f"{column.get('high_cardinality', False)}"
                    )

                    top_values = column.get("top_values") or []

                    if top_values:
                        st.dataframe(
                            pd.DataFrame(top_values),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No non-missing category values found.")

        # Numeric correlations
        st.markdown("### Numeric correlations")

        correlations = statistical.get("numeric_correlations") or {}

        if correlations:
            st.caption(
                "Values range from -1 to +1. Positive values indicate "
                "positive association; negative values indicate negative "
                "association. Correlation does not establish causation."
            )

            st.dataframe(
                pd.DataFrame(correlations),
                use_container_width=True,
            )
        else:
            st.info(
                "Correlation analysis requires eligible numeric columns "
                "with sufficient overlapping observations."
            )

        # Statistical notes
        notes = statistical.get("notes") or []

        if notes:
            with st.expander("How to interpret the statistics"):
                for note in notes:
                    st.write(f"- {note}")

    else:
        st.warning(
            "Statistical analysis was not found in the backend response."
        )

        with st.expander("Troubleshoot missing statistical analysis"):
            st.write("Top-level API response keys:")
            st.code(str(list(result.keys())))

            st.write("Summary response keys:")
            st.code(str(list(summary.keys())))

            st.write(
                "If statistical_analysis is absent from both locations, "
                "check src/validation.py and src/api.py, then redeploy "
                "the backend on Render."
            )

    # ----------------------------------------------
    # Validation analytics
    # ----------------------------------------------

    st.divider()
    st.header("Validation analytics")

    st.caption(
        "Findings are rule-generated flags that may require investigation. "
        "They are not necessarily confirmed errors."
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### Findings by severity")

        if severity_counts:
            st.bar_chart(pd.DataFrame({"Findings": severity_counts}))
        else:
            st.info("No findings by severity to display.")

    with chart_col2:
        st.markdown("### Findings by validation rule")

        if rule_counts:
            rule_df = pd.DataFrame(
                {"Findings": rule_counts}
            ).sort_values("Findings", ascending=True)

            st.bar_chart(rule_df)
        else:
            st.info("No validation-rule findings to display.")

    # ----------------------------------------------
    # Rule-level evidence
    # ----------------------------------------------

    st.divider()
    st.header("Rule-level evidence")

    rule_evidence = evidence.get("rule_evidence") or []

    if rule_evidence:
        st.caption(
            "Evidence is grouped by validation rule. "
            "The backend may limit the number of examples shown."
        )

        for item in rule_evidence:
            rule_name = item.get("rule", "Unknown rule")
            finding_count = item.get("finding_count", 0)

            with st.expander(
                f"{rule_name} — {finding_count} finding(s)"
            ):
                st.write("**Severity breakdown**")
                st.json(item.get("severity_breakdown") or {})

                examples = item.get("evidence") or []

                if examples:
                    st.write("**Example findings**")
                    st.dataframe(
                        pd.DataFrame(examples),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No example findings were supplied.")

                omitted = item.get("additional_findings_omitted", 0)

                if omitted:
                    st.caption(
                        f"{omitted} additional finding(s) omitted "
                        "from this preview."
                    )
    else:
        st.info("No rule-level evidence was returned by the backend.")

    # ----------------------------------------------
    # Findings explorer
    # ----------------------------------------------

    st.divider()
    st.header("Explore findings")

    if issues:
        findings_df = pd.DataFrame(issues)

        filter_col1, filter_col2 = st.columns([1, 2])

        if "severity" in findings_df.columns:
            available_severities = sorted(
                findings_df["severity"].dropna().unique().tolist()
            )
        else:
            available_severities = []

        if "rule" in findings_df.columns:
            available_rules = sorted(
                findings_df["rule"].dropna().unique().tolist()
            )
        else:
            available_rules = []

        with filter_col1:
            selected_severities = st.multiselect(
                "Filter by severity",
                options=available_severities,
                default=available_severities,
            )

        with filter_col2:
            selected_rules = st.multiselect(
                "Filter by validation rule",
                options=available_rules,
                default=available_rules,
            )

        search_text = st.text_input(
            "Search findings",
            placeholder="Search by record ID, name, or keyword...",
        )

        filtered_df = findings_df.copy()

        if "severity" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["severity"].isin(selected_severities)
            ]

        if "rule" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["rule"].isin(selected_rules)
            ]

        if search_text.strip():
            searchable = (
                filtered_df.fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
            )

            filtered_df = filtered_df[
                searchable.str.contains(
                    search_text.strip(),
                    case=False,
                    regex=False,
                )
            ]

        preferred_columns = [
            "company_id",
            "company_name",
            "rule",
            "severity",
            "message",
        ]

        display_columns = [
            column
            for column in preferred_columns
            if column in filtered_df.columns
        ]

        if not display_columns:
            display_columns = filtered_df.columns.tolist()

        st.caption(
            f"Showing {len(filtered_df)} of {len(findings_df)} findings"
        )

        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download filtered findings (CSV)",
            data=filtered_df[display_columns].to_csv(index=False),
            file_name="filtered_data_quality_findings.csv",
            mime="text/csv",
        )

    else:
        st.success("No validation findings were reported.")

    # ----------------------------------------------
    # Business quality report
    # ----------------------------------------------

    st.divider()
    st.header("Business quality report")

    st.caption(
        "Numerical values should be verified against the statistical "
        "results and validation findings. AI-generated recommendations "
        "should be reviewed before being acted upon."
    )

    if report:
        with st.expander("View full report", expanded=True):
            st.markdown(report)

        st.download_button(
            "Download report (Markdown)",
            data=report,
            file_name="data_quality_report.md",
            mime="text/markdown",
        )
    else:
        st.info("No business quality report was returned.")

    # ----------------------------------------------
    # Structured JSON download
    # ----------------------------------------------

    st.divider()
    st.header("Export results")

    structured_result = {
        "status": result.get("status", "unknown"),
        "ai_status": ai_status,
        "summary": summary,
        "statistical_analysis": statistical,
        "issues": issues,
        "evidence": evidence,
        "report": report,
    }

    st.download_button(
        "Download structured results (JSON)",
        data=json.dumps(
            structured_result,
            indent=2,
            default=str,
        ),
        file_name="data_quality_results.json",
        mime="application/json",
    )

else:
    st.info(
        "Your dashboard is ready. Upload a CSV above and select "
        "**Analyze dataset** to begin."
    )
